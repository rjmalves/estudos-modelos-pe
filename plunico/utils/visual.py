from modelos.cenario import Cenario
from modelos.uhe import UHE
from modelos.ute import UTE

import os
import csv
import numpy as np  # type: ignore
from typing import List
import matplotlib.pyplot as plt  # type: ignore


class Visual:
    """
    Coletânea de recursos para geração de gráficos relacionados
    às soluções dos problemas de otimização.
    """
    def __init__(self,
                 uhes: List[UHE],
                 utes: List[UTE],
                 caminho: str,
                 cenarios: List[Cenario]):
        self.uhes = uhes
        self.utes = utes
        # O caminho base já contém NOME_ESTUDO/MÉTODO/EPOCH/
        self.caminho = caminho
        self.cenarios = cenarios

    def visualiza(self):
        """
        Exporta os gráficos para visualização das saídas do problema
        de otimização.
        """
        self.visualiza_volume_final()
        self.visualiza_volume_turbinado()
        self.visualiza_volume_vertido()
        self.visualiza_afluencias()
        self.visualiza_custo_agua()
        self.visualiza_geracao_termica()
        self.visualiza_deficit()
        self.visualiza_cmo()
        self.visualiza_ci()

    def visualiza_volume_final(self):
        """
        Gera os gráficos para acompanhamento dos volumes finais.
        """
        # Se o diretório para os volumes finais não existe, cria
        caminho = self.caminho + "volume_final/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UHE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        for i, uh in enumerate(self.uhes):
            # Configurações gerais do gráfico
            plt.figure(figsize=(12, 6))
            plt.title("VOLUME FINAL PARA {}".format(uh.nome))
            # Eixo x:
            plt.xlabel("Período de estudo")
            x = np.arange(1, n_periodos + 1, 1)
            plt.xticks(x)
            # Eixo y:
            plt.ylabel("Volume final (hm3)")
            dados = [x]
            cabecalho = ["PERIODO"]
            for j, cen in enumerate(self.cenarios):
                dados.append(cen.volumes_finais[i])
                cabecalho.append("VF_CENARIO_{}".format(j + 1))
                plt.plot(x,
                         cen.volumes_finais[i],
                         color=cmap(j / n_cenarios),
                         marker="o",
                         linewidth=4,
                         alpha=0.2,
                         label="Cenário {}".format(j + 1))
            # Salva a imagem
            caminho_saida = caminho + uh.nome
            plt.savefig(caminho_saida + ".png")
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_volume_turbinado(self):
        """
        Gera os gráficos para acompanhamento dos volumes turbinados.
        """
        # Se o diretório para os volumes turbinados não existe, cria
        caminho = self.caminho + "volume_turbinado/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UHE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        for i, uh in enumerate(self.uhes):
            # Configurações gerais do gráfico
            plt.figure(figsize=(12, 6))
            plt.title("VOLUME TURBINADO PARA {}".format(uh.nome))
            # Eixo x:
            plt.xlabel("Período de estudo")
            x = np.arange(1, n_periodos + 1, 1)
            plt.xticks(x)
            # Eixo y:
            plt.ylabel("Volume turbinado (hm3)")
            dados = [x]
            cabecalho = ["PERIODO"]
            for j, cen in enumerate(self.cenarios):
                dados.append(cen.volumes_turbinados[i])
                cabecalho.append("VT_CENARIO_{}".format(j + 1))
                plt.plot(x,
                         cen.volumes_turbinados[i],
                         color=cmap(j / n_cenarios),
                         marker="o",
                         linewidth=4,
                         alpha=0.2,
                         label="Cenário {}".format(j + 1))
            # Salva a imagem
            caminho_saida = caminho + uh.nome
            plt.savefig(caminho_saida + ".png")
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_volume_vertido(self):
        """
        Gera os gráficos para acompanhamento dos volumes vertidos.
        """
        # Se o diretório para os volumes vertidos não existe, cria
        caminho = self.caminho + "volume_vertido/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UHE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        for i, uh in enumerate(self.uhes):
            # Configurações gerais do gráfico
            plt.figure(figsize=(12, 6))
            plt.title("VOLUME VERTIDO PARA {}".format(uh.nome))
            # Eixo x:
            plt.xlabel("Período de estudo")
            x = np.arange(1, n_periodos + 1, 1)
            plt.xticks(x)
            # Eixo y:
            plt.ylabel("Volume vertido (hm3)")
            dados = [x]
            cabecalho = ["PERIODO"]
            for j, cen in enumerate(self.cenarios):
                dados.append(cen.volumes_vertidos[i])
                cabecalho.append("VV_CENARIO_{}".format(j + 1))
                plt.plot(x,
                         cen.volumes_vertidos[i],
                         color=cmap(j / n_cenarios),
                         marker="o",
                         linewidth=4,
                         alpha=0.2,
                         label="Cenário {}".format(j + 1))
            # Salva a imagem
            caminho_saida = caminho + uh.nome
            plt.savefig(caminho_saida + ".png")
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_afluencias(self):
        """
        Gera os gráficos para acompanhamento das afluências.
        """
        # Se o diretório para as afluências não existe, cria
        caminho = self.caminho + "afluencias/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UHE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        for i, uh in enumerate(self.uhes):
            # Configurações gerais do gráfico
            plt.figure(figsize=(12, 6))
            plt.title("AFLUÊNCIAS PARA {}".format(uh.nome))
            # Eixo x:
            plt.xlabel("Período de estudo")
            x = np.arange(1, n_periodos + 1, 1)
            plt.xticks(x)
            # Eixo y:
            plt.ylabel("Volume (hm3)")
            dados = [x]
            cabecalho = ["PERIODO"]
            for j, cen in enumerate(self.cenarios):
                dados.append(cen.afluencias[i])
                cabecalho.append("AFL_CENARIO_{}".format(j + 1))
                plt.plot(x,
                         cen.afluencias[i],
                         color=cmap(j / n_cenarios),
                         marker="o",
                         linewidth=4,
                         alpha=0.2,
                         label="Cenário {}".format(j + 1))
            # Salva a imagem
            caminho_saida = caminho + uh.nome
            plt.savefig(caminho_saida + ".png")
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_custo_agua(self):
        """
        Gera os gráficos para acompanhamento do CMA.
        """
        # Se o diretório para o CMA não existe, cria
        caminho = self.caminho + "CMA/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UHE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        for i, uh in enumerate(self.uhes):
            # Configurações gerais do gráfico
            plt.figure(figsize=(12, 6))
            plt.title("CMA PARA {}".format(uh.nome))
            # Eixo x:
            plt.xlabel("Período de estudo")
            x = np.arange(1, n_periodos + 1, 1)
            plt.xticks(x)
            # Eixo y:
            plt.ylabel("Variação do custo ($/hm3)")
            dados = [x]
            cabecalho = ["PERIODO"]
            for j, cen in enumerate(self.cenarios):
                dados.append(cen.custo_agua[i])
                cabecalho.append("CMA_CENARIO_{}".format(j + 1))
                plt.plot(x,
                         cen.custo_agua[i],
                         color=cmap(j / n_cenarios),
                         marker="o",
                         linewidth=4,
                         alpha=0.2,
                         label="Cenário {}".format(j + 1))
            # Salva a imagem
            caminho_saida = caminho + uh.nome
            plt.savefig(caminho_saida + ".png")
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_geracao_termica(self):
        """
        Gera os gráficos para acompanhamento da geração das térmicas.
        """
        # Se o diretório para as térmicas não existe, cria
        caminho = self.caminho + "geracao_termica/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UTE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        for i, ut in enumerate(self.utes):
            # Configurações gerais do gráfico
            plt.figure(figsize=(12, 6))
            plt.title("GERAÇÂO TÉRMICA PARA {}".format(ut.nome))
            # Eixo x:
            plt.xlabel("Período de estudo")
            x = np.arange(1, n_periodos + 1, 1)
            plt.xticks(x)
            # Eixo y:
            dados = [x]
            cabecalho = ["PERIODO"]
            for j, cen in enumerate(self.cenarios):
                dados.append(cen.geracao_termica[i])
                cabecalho.append("GT_CENARIO_{}".format(j + 1))
                plt.plot(x,
                         cen.geracao_termica[i],
                         color=cmap(j / n_cenarios),
                         marker="o",
                         linewidth=4,
                         alpha=0.2,
                         label="Cenário {}".format(j + 1))
            # Salva a imagem
            caminho_saida = caminho + ut.nome
            plt.savefig(caminho_saida + ".png")
            self.exporta_dados(caminho_saida, cabecalho, dados)
            plt.close()

    def visualiza_deficit(self):
        """
        Gera os gráficos para acompanhamento do déficit.
        """
        # Se o diretório para os déficits não existe, cria
        caminho = self.caminho + "deficit/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UTE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        # Configurações gerais do gráfico
        plt.figure(figsize=(12, 6))
        plt.title("DÉFICITS")
        # Eixo x:
        plt.xlabel("Período de estudo")
        x = np.arange(1, n_periodos + 1, 1)
        plt.xticks(x)
        # Eixo y:
        plt.ylabel("Geração (MWmed)")
        dados = [x]
        cabecalho = ["PERIODO"]
        for j, cen in enumerate(self.cenarios):
            dados.append(cen.deficit)
            cabecalho.append("DEFICIT_CENARIO_{}".format(j + 1))
            plt.plot(x,
                     cen.deficit,
                     color=cmap(j / n_cenarios),
                     marker="o",
                     linewidth=4,
                     alpha=0.2,
                     label="Cenário {}".format(j + 1))
        # Salva a imagem
        caminho_saida = caminho + "deficit"
        plt.savefig(caminho_saida + ".png")
        self.exporta_dados(caminho_saida, cabecalho, dados)
        plt.close()

    def visualiza_cmo(self):
        """
        Gera os gráficos para acompanhamento do CMO.
        """
        # Se o diretório para o CMO não existe, cria
        caminho = self.caminho + "CMO/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UTE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        # Configurações gerais do gráfico
        plt.figure(figsize=(12, 6))
        plt.title("CUSTO MARGINAL DE OPERAÇÂO")
        # Eixo x:
        plt.xlabel("Período de estudo")
        x = np.arange(1, n_periodos + 1, 1)
        plt.xticks(x)
        # Eixo y:
        plt.ylabel("Variação do Custo ($/MWmed)")
        dados = [x]
        cabecalho = ["PERIODO"]
        for j, cen in enumerate(self.cenarios):
            dados.append(cen.cmo)
            cabecalho.append("CMO_CENARIO_{}".format(j + 1))
            plt.plot(x,
                     cen.cmo,
                     color=cmap(j / n_cenarios),
                     marker="o",
                     linewidth=4,
                     alpha=0.2,
                     label="Cenário {}".format(j + 1))
        # Salva a imagem
        caminho_saida = caminho + "cmo"
        plt.savefig(caminho_saida + ".png")
        self.exporta_dados(caminho_saida, cabecalho, dados)
        plt.close()

    def visualiza_ci(self):
        """
        Gera os gráficos para acompanhamento do CI.
        """
        # Se o diretório para o CI não existe, cria
        caminho = self.caminho + "custo_imediato/"
        if not os.path.exists(caminho):
            os.makedirs(caminho)
        # Um gráfico de saída para cada UTE
        n_periodos = len(self.cenarios[0].volumes_finais[0])
        n_cenarios = len(self.cenarios)
        cmap = plt.get_cmap('viridis')
        # Configurações gerais do gráfico
        plt.figure(figsize=(12, 6))
        plt.title("CUSTO IMEDIATO DE OPERAÇÂO")
        # Eixo x:
        plt.xlabel("Período de estudo")
        x = np.arange(1, n_periodos + 1, 1)
        plt.xticks(x)
        # Eixo y:
        plt.ylabel("Custo ($)")
        dados = [x]
        cabecalho = ["PERIODO"]
        for j, cen in enumerate(self.cenarios):
            dados.append(cen.ci)
            cabecalho.append("CI_CENARIO_{}".format(j + 1))
            plt.plot(x,
                     cen.ci,
                     color=cmap(j / n_cenarios),
                     marker="o",
                     linewidth=4,
                     alpha=0.2,
                     label="Cenário {}".format(j + 1))
        # Salva a imagem
        caminho_saida = caminho + "ci"
        plt.savefig(caminho_saida + ".png")
        self.exporta_dados(caminho_saida, cabecalho, dados)
        plt.close()

    def exporta_dados(self,
                      caminho: str,
                      cabecalhos: List[str],
                      dados: List[list]):
        """
        Exporta um conjunto de dados de uma determinada visualização
        para um formato CSV.
        """
        # Confere se o número de cabeçalhos é igual ao de dados
        n_dados = len(dados[0])
        # Confere se a quantidade de entradas de cada dado é igual
        arq = caminho + ".csv"
        with open(arq, "w", newline="") as arqcsv:
            escritor = csv.writer(arqcsv,
                                  delimiter=",",
                                  quotechar="|",
                                  quoting=csv.QUOTE_MINIMAL)
            escritor.writerow(cabecalhos)
            for i in range(n_dados):
                escritor.writerow([d[i] for d in dados])
