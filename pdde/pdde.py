from modelos.cortebenders import CorteBenders
from modelos.penteafluencias import PenteAfluencias
from modelos.cenario import Cenario
from modelos.resultado import Resultado
from utils.leituraentrada import LeituraEntrada

import logging
import coloredlogs  # type: ignore
from typing import List, Tuple
import numpy as np  # type: ignore
from statistics import pstdev, mean
from cvxopt.modeling import variable, op, solvers, _function  # type: ignore
solvers.options['glpk'] = {'msg_lev': 'GLP_MSG_OFF'}
logger = logging.getLogger(__name__)


class PDDE:
    """
    Coletânea de métodos para solução de um estudo de
    planejamento energético através de Programação
    Dinâmica Dual Estocástica.
    """
    def __init__(self, e: LeituraEntrada, LOG_LEVEL: str):
        self.cfg = e.cfg
        self.uhes = e.uhes
        self.utes = e.utes
        self.demandas = e.demandas
        coloredlogs.install(logger=logger, level=LOG_LEVEL)
        self.pente = PenteAfluencias(e)
        self.pente.monta_pente_afluencias()
        self.sim_final = PenteAfluencias(e)
        self.cenarios: List[Cenario] = []
        self.z_sup: List[float] = []
        self.z_inf: List[float] = []

    def __monta_pl(self,
                   pente: PenteAfluencias,
                   dente: int,
                   periodo: int,
                   abertura: int = -1) -> op:
        """
        Realiza a configuração das variáveis e restrições de um
        problema de otimização a ser realizado no problema de PDDD.
        """
        # ----- Variáveis -----
        self.vf = variable(len(self.uhes), "Volume final (hm3)")
        self.vt = variable(len(self.uhes), "Volume turbinado (hm3)")
        self.vv = variable(len(self.uhes), "Volume vertido (hm3)")
        self.gt = variable(len(self.utes), "Geração térmica (MWmed)")
        self.deficit = variable(1, "Déficit (MWmed)")
        self.alpha = variable(1, "Custo futuro ($)")

        # ----- Função objetivo -----
        self.func_objetivo: _function = 0
        for i, ut in enumerate(self.utes):
            self.func_objetivo += ut.custo * self.gt[i]

        self.func_objetivo += self.cfg.custo_deficit * self.deficit[0]

        for i in range(len(self.uhes)):
            self.func_objetivo += 0.01 * self.vv[i]

        self.func_objetivo += 1.0 * self.alpha[0]

        # ----- Restrições -----
        self.cons: List[_function] = []
        # Balanço hídrico
        for i, uh in enumerate(self.uhes):
            if periodo == 0:
                # O volume inicial é dado no problema
                vi = float(uh.vol_inicial)
            else:
                # O volume inicial é o final do nó anterior
                vi = float(pente.dentes[dente][periodo - 1]
                           .volumes_finais[i])
            # Se está executando a FORWARD, a afluência é a do nó
            # anterior no mesmo dente. Caso contrário, é da abertura
            # passada à função de montar o PL.
            if abertura == -1:
                afl = float(pente.dentes[dente][periodo]
                            .afluencias[i])
            else:
                afl = float(pente
                            .afluencias_abertura(periodo, abertura)[i])
            self.cons.append(self.vf[i] == vi + afl - self.vt[i] - self.vv[i])

        # Atendimento à demanda
        gerado = 0
        for i, uh in enumerate(self.uhes):
            gerado += float(uh.produtividade) * self.vt[i]
        for i, ut in enumerate(self.utes):
            gerado += self.gt[i]
        gerado += self.deficit[0]
        self.cons.append(gerado == float(self.demandas[periodo].demanda))
        # Restrições operacionais
        for i, uh in enumerate(self.uhes):
            # Volume útil do reservatório
            self.cons.append(self.vf[i] <= uh.vol_maximo)
            self.cons.append(self.vf[i] >= uh.vol_minimo)
            # Engolimento máximo
            self.cons.append(self.vt[i] <= uh.engolimento)
            # Factibilidade do problema
            self.cons.append(self.vt[i] >= 0)
            self.cons.append(self.vv[i] >= 0)
        for i, ut in enumerate(self.utes):
            # Geração mínima e máxima de térmica
            self.cons.append(self.gt[i] >= 0)
            self.cons.append(self.gt[i] <= ut.capacidade)
        # Factibilidade do problema
        self.cons.append(self.deficit[0] >= 0)

        # Cortes de Benders - exceto se estiver no último período
        self.cons.append(self.alpha[0] >= 0)
        if periodo == self.cfg.n_periodos - 1:
            return
        num_uhes = len(self.uhes)
        # Adiciona os cortes do próximo nó, no mesmo dente
        no_futuro = pente.dentes[dente][periodo + 1]
        for corte in no_futuro.cortes:
            eq = 0.
            for i_uhe in range(num_uhes):
                eq += float(corte.coef_angular[i_uhe]) * self.vf[i_uhe]
            eq += float(corte.termo_indep)
            self.cons.append(self.alpha[0] >= eq)

    def resolve_pdde(self) -> Resultado:
        """
        Resolve um problema de planejamento energético através da
        PDDE.
        """
        # Erros e condição de parada
        logger.info("# RESOLVENDO PROBLEMA DE PDDE #")
        logger.info("X----X-------------------X-------------------X")
        logger.info("  IT        Z_SUP                 Z_INF       ")
        it = 0
        self.intervalo_conf: List[Tuple[float, float]] = []
        while True:
            # Realiza, para cada dente, a parte FORWARD
            if self.cfg.reamostrar and it > 0:
                self.pente.reamostrar()
            for p in range(self.cfg.n_periodos):
                for d, dente in enumerate(self.pente.dentes):
                    self.__monta_pl(self.pente, d, p)
                    self.pl = op(self.func_objetivo, self.cons)
                    self.pl.solve("dense", "glpk")
                    # Armazena as saídas obtidas no PL no objeto nó
                    self.__armazena_saidas(self.pente, d, p)
            # Condição de saída por convergência
            if self.__verifica_convergencia(it):
                break
            it += 1
            # Condição de saída por iterações
            if it >= self.cfg.max_iter:
                logger.warning("   LIMITE DE ITERAÇÕES ATINGIDO!")
                break
            # Realiza, para cada dente, a parte BACKWARD
            for p in range(self.cfg.n_periodos - 1, -1, -1):
                cortes_periodo: List[CorteBenders] = []
                for d, _ in enumerate(self.pente.dentes):
                    # A BACKWARD na PDDE, para obter um corte,
                    # na verdade é constituída de múltiplos problemas
                    # de despacho e o corte é o médio de todas.
                    cortes_no: List[CorteBenders] = []
                    for a in range(self.cfg.aberturas_periodo):
                        self.__monta_pl(self.pente, d, p, a)
                        self.pl = op(self.func_objetivo, self.cons)
                        self.pl.solve("dense", "glpk")
                        # Armazena as saídas obtidas no nó
                        self.__armazena_saidas(self.pente, d, p)
                        # Armazena o corte produzido pelo nó
                        cortes_no.append(self.__obtem_corte(d, p))
                    # Cria o corte médio para o nó, referente ao dente
                    cortes_periodo.append(self.__cria_corte(cortes_no))
                # Adiciona os cortes do período para os nós do período,
                # em cada dente
                for d, dente in enumerate(self.pente.dentes):
                    for c in cortes_periodo:
                        self.pente.dentes[d][p].adiciona_corte(c)
        # Terminando o loop do método, realiza a simulação final e
        # organiza os cenários de saída
        logger.info("X----X-------------------X-------------------X")
        self.__simulacao_final()
        logger.info("# FIM DA SOLUÇÃO #")
        logger.info("----------------------------------------")
        return Resultado(self.cfg,
                         self.uhes,
                         self.utes,
                         self.sim_final.organiza_cenarios(),
                         self.z_sup,
                         self.z_inf,
                         self.intervalo_conf,
                         self.__organiza_cortes())

    def __obtem_corte(self, d: int, p: int) -> CorteBenders:
        """
        Obtém o corte de Benders a partir do resultado de um PL
        backward da PDDE.
        """
        no = self.pente.dentes[d][p]
        coef_angular: List[float] = []
        termo_indep = no.custo_total
        for i, uh in enumerate(self.uhes):
            coef_angular.append(-no.custo_agua[i])
            if p == 0:
                vi = uh.vol_inicial
            else:
                ant = self.pente.dentes[d][p - 1]
                vi = ant.volumes_finais[i]
            termo_indep -= vi * coef_angular[i]
        corte = CorteBenders(coef_angular, termo_indep, no.custo_total)
        return corte

    def __cria_corte(self,
                     cortes: List[CorteBenders]) -> CorteBenders:
        """
        Armazena o corte de Benders médio para um nó.
        """
        num_uhes = len(self.uhes)
        num_cortes = self.cfg.aberturas_periodo

        # Calcula o corte médio, considerando cauda e não-cauda
        coef_ang_medio = np.zeros((num_uhes,))
        termo_indep_medio = 0.
        for i, corte in enumerate(cortes):
            # Calcula o coeficente angular médio
            for i_uhe in range(num_uhes):
                coef_ang_medio[i_uhe] += corte.coef_angular[i_uhe] / num_cortes
            # Calcula o termo independente médio
            termo_indep_medio += corte.termo_indep / num_cortes

        # Obtém o número de cortes na cauda
        num_cauda = int(self.cfg.aberturas_cauda * self.cfg.aberturas_periodo)
        # Ordena os cortes e extrai os cortes da cauda
        cortes_ordenados = sorted(cortes, reverse=True)
        cortes_cauda = cortes_ordenados[:num_cauda]
        # Calcula o corte médio da cauda
        coef_ang_cauda = np.zeros((num_uhes,))
        termo_indep_cauda = 0.
        for i, corte in enumerate(cortes_cauda):
            # Calcula o coeficiente angular médio
            for i_uhe in range(num_uhes):
                coef_ang_cauda[i_uhe] += corte.coef_angular[i_uhe] / num_cauda
            # Calcula o termo independente médio
            termo_indep_cauda += corte.termo_indep / num_cauda

        # Pondera os cortes médios da cauda e não-cauda
        lmbda = self.cfg.peso_cauda
        coef_ang_ponderado = list((1 - lmbda) * coef_ang_medio
                                  + lmbda * coef_ang_cauda)
        termo_indep_ponderado = ((1 - lmbda) * termo_indep_medio
                                 + lmbda * termo_indep_cauda)
        corte_ponderado = CorteBenders(coef_ang_ponderado,
                                       termo_indep_ponderado,
                                       0.0)
        return corte_ponderado

    def __verifica_convergencia(self, it: int) -> bool:
        """
        Verifica se houve a convergência para a PDDE, conferindo
        os limites inferior e superior, bem como o intervalo de
        confiança.
        """
        # Calcula o Z_inf
        z_inf = mean([d[0].custo_total for d in self.pente.dentes])
        self.z_inf.append(z_inf)
        # Obtém os custos imediatos para cada nó de cada dente
        custos_imediatos: List[List[float]] = []
        for dente in self.pente.dentes:
            custos_imediatos_dente = [n.custo_total - n.custo_futuro
                                      for n in dente]
            custos_imediatos.append(custos_imediatos_dente)
        # Calcula o Z_sup
        custos_dente = [sum(custo_dente)
                        for custo_dente in custos_imediatos]
        z_sup = mean(custos_dente)
        self.z_sup.append(z_sup)
        # Calcula o intervalo de confiança
        desvio = pstdev(custos_dente)
        conf = self.cfg.intervalo_conf
        tol = 1e-8
        limite_inf = max([1e-3, z_sup - conf * desvio - tol])
        limite_sup = z_sup + conf * desvio + tol
        self.intervalo_conf.append((limite_inf, limite_sup))

        # Mínimo de iterações
        n_it = len(self.z_inf)
        logger.info(" {:4}    {:16.6f}    {:16.6f}".
                    format(it + 1, z_sup, z_inf))
        if n_it < self.cfg.min_iter:
            return False

        # Estabilidade do Z_inf por algumas iterações
        erros = [self.z_inf[i] for i in range(-self.cfg.min_iter, 0)]
        if max(erros) - min(erros) < self.cfg.intervalo_conf * z_inf:
            logger.info("   >> CONVERGIU <<: Estabilidade do Z_INF!!")
            return True

        return False

    def __armazena_saidas(self, pente: PenteAfluencias, d: int, p: int):
        """
        Processa as saídas do problema e armazena nos nós.
        """
        vol_finais: List[float] = []
        vol_turbinados: List[float] = []
        vol_vertidos: List[float] = []
        custo_agua: List[float] = []
        geracao_termica: List[float] = []
        for i, uh in enumerate(self.uhes):
            vol_finais.append(self.vf[i].value()[0])
            vol_turbinados.append(self.vt[i].value()[0])
            vol_vertidos.append(self.vv[i].value()[0])
            custo_agua.append(self.cons[i].multiplier.value[0])
        for i, ut in enumerate(self.utes):
            geracao_termica.append(self.gt[i].value()[0])
        deficit = self.deficit[0].value()[0]
        c_cmo = len(self.uhes)
        cmo = abs(self.cons[c_cmo].multiplier.value[0])
        alpha = self.alpha[0].value()[0]
        f_obj = self.func_objetivo.value()[0]
        pente.dentes[d][p].preenche_resultados(vol_finais,
                                               vol_turbinados,
                                               vol_vertidos,
                                               custo_agua,
                                               geracao_termica,
                                               deficit,
                                               cmo,
                                               f_obj - alpha,
                                               alpha,
                                               f_obj)

    def __simulacao_final(self):
        """
        """
        logger.info("            # SIMULAÇÂO FINAL #")
        logger.info("X-------------------X-------------------X")
        logger.info("       Z_SUP                Z_INF       ")
        self.sim_final.monta_simulacao_final(self.pente)
        # Realiza uma "forward"
        for p in range(self.cfg.n_periodos):
            for d, _ in enumerate(self.sim_final.dentes):
                self.__monta_pl(self.sim_final, d, p)
                self.pl = op(self.func_objetivo, self.cons)
                self.pl.solve("dense", "glpk")
                # Armazena as saídas obtidas no PL no objeto nó
                self.__armazena_saidas(self.sim_final, d, p)

        # Calcula o Z_inf
        z_inf = mean([d[0].custo_total for d in self.sim_final.dentes])
        self.z_inf.append(z_inf)
        # Obtém os custos imediatos para cada nó de cada dente
        custos_imediatos: List[List[float]] = []
        for dente in self.sim_final.dentes:
            custos_imediatos_dente = [n.custo_total - n.custo_futuro
                                      for n in dente]
            custos_imediatos.append(custos_imediatos_dente)
        # Calcula o Z_sup
        custos_dente = [sum(custo_dente)
                        for custo_dente in custos_imediatos]
        z_sup = mean(custos_dente)
        self.z_sup.append(z_sup)

        logger.info(" {:19.6f} {:19.6f}".format(z_sup, z_inf))
        logger.info("X-------------------X-------------------X")

    def __organiza_cortes(self) -> List[List[List[CorteBenders]]]:
        """
        """
        cortes: List[List[List[CorteBenders]]] = []
        for p in range(self.cfg.n_periodos):
            cortes.append([self.pente.dentes[0][p].cortes])
        return cortes
