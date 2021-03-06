from modelos.cortebenders import CorteBenders
from modelos.cenario import Cenario
from utils.leituraentrada import LeituraEntrada
from modelos.no import No

from copy import deepcopy
from typing import List
from itertools import product


class ArvoreAfluencias:
    """
    Árvore organizada das afluências que definem os cenários
    existentes em um problema de PL Único ou PDDD a ser resolvido.
    """
    def __init__(self, e: LeituraEntrada):
        self.n_periodos = e.cfg.n_periodos
        self.aberturas_periodo = e.cfg.aberturas_periodo
        self.n_pos_estudo = e.cfg.n_pos_estudo
        self.n_uhes = e.cfg.n_uhes
        self.vis = [uh.vol_inicial for uh in e.uhes]
        self.afluencias = deepcopy(e.afluencias)
        self.nos_por_periodo: List[int] = []
        self.arvore: List[List[No]] = []

    def monta_arvore_afluencias(self):
        """
        Monta uma árvore de afluências a partir dos dados lidos
        do arquivo de configuração. A árvore é uma lista composta,
        onde acessar o índice [i][j][k] significa:

        i: ID da UHE

        j: ramo da árvore da UHE i

        k: nó do ramo j
        """
        na = self.aberturas_periodo
        # Limite as afluências de cada UHE para o número de aberturas
        for i in range(1, self.n_uhes + 1):
            # O primeiro período tem apenas uma possível afluência
            self.afluencias[i][0] = [self.afluencias[i][0][0]]
            for e in range(1, self.n_periodos):
                self.afluencias[i][e] = self.afluencias[i][e][:na]
        # Para cada período de estudo, lista as combinações de afluências
        combs_periodo: List[List[float]] = []
        for p in range(self.n_periodos):
            # Varre as afluências de cada UHE
            afls_periodo: List[float] = []
            for i in range(1, self.n_uhes + 1):
                afls_periodo.append(self.afluencias[i][p])
            # Faz o produto para extrair as combinações
            combinacoes = product(*[a for a in afls_periodo])
            combs_periodo.append([list(c) for c in combinacoes])
        # Constroi a árvore a partir das combinações de cada período
        # O primeiro período tem apenas 1 nó:
        l_no: List[No] = [No(combs_periodo[0][0])]
        self.arvore.append(l_no)
        # Cada período seguinte multiplica o número de nós do período
        # anterior pelo número de combinações do próprio
        for p in range(1, self.n_periodos):
            nos_periodo: List[No] = []
            for nos_periodo_anterior in range(len(self.arvore[p - 1])):
                for comb_periodo in combs_periodo[p]:
                    nos_periodo.append(No(comb_periodo))
            self.arvore.append(nos_periodo)
        # Faz a contagem de nós por período
        for a in self.arvore:
            self.nos_por_periodo.append(len(a))
        # Força os volumes iniciais do nó do primeiro período
        self.arvore[0][0].volumes_iniciais = self.vis

    def monta_simulacao_final(self, arvore):
        """
        """
        arvore_atual: ArvoreAfluencias = arvore
        for i in range(1, self.n_uhes + 1):
            # O primeiro período tem apenas uma possível afluência
            self.afluencias[i][0] = [self.afluencias[i][0][0]]
        # Para cada período de estudo, lista as combinações de afluências
        combs_periodo: List[List[float]] = []
        for p in range(self.n_periodos):
            # Varre as afluências de cada UHE
            afls_periodo: List[float] = []
            for i in range(1, self.n_uhes + 1):
                afls_periodo.append(self.afluencias[i][p])
            # Faz o produto para extrair as combinações
            combinacoes = product(*[a for a in afls_periodo])
            combs_periodo.append([list(c) for c in combinacoes])
        # Constroi a árvore a partir das combinações de cada período
        # O primeiro período tem apenas 1 nó:
        l_no: List[No] = [No(combs_periodo[0][0])]
        self.arvore.append(l_no)
        # Cada período seguinte multiplica o número de nós do período
        # anterior pelo número de combinações do próprio
        for p in range(1, self.n_periodos):
            nos_periodo: List[No] = []
            for nos_periodo_anterior in range(len(self.arvore[p - 1])):
                for comb_periodo in combs_periodo[p]:
                    nos_periodo.append(No(comb_periodo))
            self.arvore.append(nos_periodo)
        # Faz a contagem de nós por período
        for a in self.arvore:
            self.nos_por_periodo.append(len(a))
        # Força os volumes iniciais do nó do primeiro período
        self.arvore[0][0].volumes_iniciais = self.vis
        # Copia os cortes de cada nó da execução anterior
        for p in range(self.n_periodos):
            # Acumula todos os cortes para o período
            cortes_p: List[CorteBenders] = []
            for no in arvore_atual.arvore[p]:
                cortes_p += no.cortes
            # Atribui todos os cortes a cada nó da árvore de
            # simulação final
            for no in self.arvore[p]:
                no.cortes = cortes_p

    def indice_no_anterior(self,
                           periodo: int,
                           indice_no: int) -> int:
        """
        Retorna o índice do nó do período anterior na árvore de afluências
        a partir de um certo nó de um período.
        """
        n_aberturas_periodo = len(self.afluencias[1][periodo])
        return int(indice_no / n_aberturas_periodo)

    def indices_proximos_nos(self, periodo: int, indice_no: int) -> List[int]:
        """
        Retorna os índices dos possíveis nós após
        """
        if periodo == self.n_periodos - 1:
            return []
        else:
            n_aberturas_periodo = len(self.afluencias[1][periodo + 1])
            indice_inicial = n_aberturas_periodo * indice_no
            indice_final = indice_inicial + n_aberturas_periodo
            return list(range(indice_inicial, indice_final))

    def organiza_cenarios(self) -> List[Cenario]:
        """
        Parte das folhas e reconstroi as séries históricas de cada variável de
        interesse para cada cenário que aconteceu no estudo realizado.
        """
        n_cenarios = self.nos_por_periodo[-1]
        cenarios: List[Cenario] = []
        for c in range(n_cenarios):
            nos_cenario: List[No] = []
            indice_no = c
            for p in range(self.n_periodos - 1, -1, -1):
                no = self.arvore[p][indice_no]
                nos_cenario.insert(0, no)
                indice_no = self.indice_no_anterior(p, indice_no)
            cen = Cenario.cenario_dos_nos(nos_cenario)
            cenarios.append(cen)
        return cenarios
