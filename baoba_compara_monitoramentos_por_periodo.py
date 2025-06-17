import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path


class ComparadorMonitoramentoPoPeriodo:
    """
    Compara dados de monitoramento entre dois períodos ― “atual” e “anterior” ―
    gerando gráficos de Ocorrências e Interações em arquivos separados.

    Parâmetros
    ----------
    df_atual : pd.DataFrame
        DataFrame com as colunas:
        - monitoramento_nome.keyword
        - total_ocorrencias
        - total_interacoes

    df_anterior : pd.DataFrame
        Mesmo layout do `df_atual`.

    output_folder : str | Path, opcional
        Pasta onde os gráficos serão salvos.  Padrão: “.” (diretório atual).
    """

    def __init__(self, df_atual: pd.DataFrame, df_anterior: pd.DataFrame,
                 output_folder: str | Path = ".") -> None:
        self.df_atual = df_atual.rename(columns={
            "total_ocorrencias": "total_ocorrencias_atual",
            "total_interacoes": "total_interacoes_atual"
        })
        self.df_anterior = df_anterior.rename(columns={
            "total_ocorrencias": "total_ocorrencias_anterior",
            "total_interacoes": "total_interacoes_anterior"
        })
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)

        self.df_merged: pd.DataFrame | None = None
        self.df_occ_melt: pd.DataFrame | None = None
        self.df_int_melt: pd.DataFrame | None = None

    # ------------------------------------------------------------------ #
    # -----------------------  ETAPA DE CÁLCULO  ----------------------- #
    # ------------------------------------------------------------------ #
    def calcular_diferencas(self) -> None:
        """Cria `self.df_merged` com diferenças e variações percentuais."""
        df = pd.merge(
            self.df_atual,
            self.df_anterior,
            on="monitoramento_nome.keyword",
            how="inner",
            suffixes=("_atual", "_anterior"),
        )

        # Diferenças absolutas
        df["diff_ocorrencias"] = (
            df["total_ocorrencias_atual"] - df["total_ocorrencias_anterior"]
        )
        df["diff_interacoes"] = (
            df["total_interacoes_atual"] - df["total_interacoes_anterior"]
        )

        # Variações percentuais
        df["perc_ocorrencias"] = (
            df["diff_ocorrencias"] / df["total_ocorrencias_anterior"]
        ) * 100
        df["perc_interacoes"] = (
            df["diff_interacoes"] / df["total_interacoes_anterior"]
        ) * 100

        self.df_merged = df

    # ------------------------------------------------------------------ #
    # ----------------------  DADOS LONGOS (melt)  ---------------------- #
    # ------------------------------------------------------------------ #
    def preparar_longos(self) -> None:
        """Gera `self.df_occ_melt` e `self.df_int_melt` a partir de `self.df_merged`."""
        if self.df_merged is None:  # garantia de execução prévia
            self.calcular_diferencas()

        # Ocorrências
        df_occ = self.df_merged[[
            "monitoramento_nome.keyword",
            "total_ocorrencias_atual",
            "total_ocorrencias_anterior",
            "diff_ocorrencias",
            "perc_ocorrencias",
        ]].copy()

        df_occ_melt = df_occ.melt(
            id_vars=["monitoramento_nome.keyword",
                     "diff_ocorrencias",
                     "perc_ocorrencias"],
            var_name="Semana",
            value_name="Ocorrencias",
        )
        df_occ_melt["Semana"] = df_occ_melt["Semana"].replace({
            "total_ocorrencias_atual": "Atual",
            "total_ocorrencias_anterior": "Anterior",
        })

        # Interações
        df_int = self.df_merged[[
            "monitoramento_nome.keyword",
            "total_interacoes_atual",
            "total_interacoes_anterior",
            "diff_interacoes",
            "perc_interacoes",
        ]].copy()

        df_int_melt = df_int.melt(
            id_vars=["monitoramento_nome.keyword",
                     "diff_interacoes",
                     "perc_interacoes"],
            var_name="Semana",
            value_name="Interacoes",
        )
        df_int_melt["Semana"] = df_int_melt["Semana"].replace({
            "total_interacoes_atual": "Atual",
            "total_interacoes_anterior": "Anterior",
        })

        self.df_occ_melt = df_occ_melt
        self.df_int_melt = df_int_melt

    # ------------------------------------------------------------------ #
    # ----------------------  FUNÇÕES DE FORMATO  ---------------------- #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _fmt_ptbr(x, _pos) -> str:
        s = f"{x:,.0f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def _format_ptbr_int(value) -> str:
        s = f"{value:,.0f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")

    # ------------------------------------------------------------------ #
    # --------------------  GRÁFICO DE OCORRÊNCIAS  --------------------- #
    # ------------------------------------------------------------------ #
    def plotar_ocorrencias(self, nome_arquivo: str = "grafico_comparativo_periodo_atual_anterior_ocorrencias.png") -> Path:
        """Gera e salva o gráfico de Ocorrências."""
        if self.df_occ_melt is None:  # garantia de execução prévia
            self.preparar_longos()

        sns.set_style("whitegrid")
        palette = {"Atual": "#00AFBB", "Anterior": "#bbdefb"}

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=self.df_occ_melt,
            y="monitoramento_nome.keyword",
            x="Ocorrencias",
            hue="Semana",
            orient="h",
            ax=ax,
            errorbar=None,
            palette=palette,
        )
        ax.set_title("Comparação de Ocorrências (Período Atual vs. Anterior)")
        ax.set_xlabel("Ocorrências")
        ax.set_ylabel("Eixo")
        ax.legend(title="Período", loc="best")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(self._fmt_ptbr))

        # Rótulos nas barras
        max_label_x = 0
        for i, bar in enumerate(ax.patches[:len(self.df_occ_melt)]):
            row = self.df_occ_melt.iloc[i]
            val_abs = row["Ocorrencias"]
            diff_perc = row["perc_ocorrencias"]
            semana = row["Semana"]

            cor = "green" if diff_perc >= 0 else "red"
            sinal = "+" if diff_perc >= 0 else ""
            if semana == "Atual":
                texto = f"{self._format_ptbr_int(val_abs)} ({sinal}{diff_perc:.1f}%)"
                cor_txt = cor
            else:
                texto = self._format_ptbr_int(val_abs)
                cor_txt = "black"

            offset = 0.02 * abs(bar.get_width())
            x_txt = bar.get_width() + offset
            y_txt = bar.get_y() + bar.get_height() / 2
            ax.text(x_txt, y_txt, texto, va="center", ha="left",
                    fontsize=9, fontweight="bold", color=cor_txt)
            max_label_x = max(max_label_x, x_txt)

        ax.set_xlim(left=0, right=max_label_x * 1.20)
        ax.tick_params(axis="x", rotation=30, labelsize=8)

        plt.tight_layout()
        caminho = self.output_folder / nome_arquivo
        plt.savefig(caminho, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return caminho

    # ------------------------------------------------------------------ #
    # --------------------  GRÁFICO DE INTERAÇÕES  ---------------------- #
    # ------------------------------------------------------------------ #
    def plotar_interacoes(self, nome_arquivo: str = "grafico_comparativo_periodo_atual_anterior_interacoes.png") -> Path:
        """Gera e salva o gráfico de Interações."""
        if self.df_int_melt is None:  # garantia de execução prévia
            self.preparar_longos()

        sns.set_style("whitegrid")
        palette = {"Atual": "#00AFBB", "Anterior": "#bbdefb"}

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            data=self.df_int_melt,
            y="monitoramento_nome.keyword",
            x="Interacoes",
            hue="Semana",
            orient="h",
            ax=ax,
            errorbar=None,
            palette=palette,
        )
        ax.set_title("Comparação de Interações (Período Atual vs. Anterior)")
        ax.set_xlabel("Interações")
        ax.set_ylabel("Eixo")
        ax.legend(title="Período", loc="best")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(self._fmt_ptbr))

        # Rótulos nas barras
        max_label_x = 0
        for i, bar in enumerate(ax.patches[:len(self.df_int_melt)]):
            row = self.df_int_melt.iloc[i]
            val_abs = row["Interacoes"]
            diff_perc = row["perc_interacoes"]
            semana = row["Semana"]

            cor = "green" if diff_perc >= 0 else "red"
            sinal = "+" if diff_perc >= 0 else ""
            if semana == "Atual":
                texto = f"{self._format_ptbr_int(val_abs)} ({sinal}{diff_perc:.1f}%)"
                cor_txt = cor
            else:
                texto = self._format_ptbr_int(val_abs)
                cor_txt = "black"

            offset = 0.02 * abs(bar.get_width())
            x_txt = bar.get_width() + offset
            y_txt = bar.get_y() + bar.get_height() / 2
            ax.text(x_txt, y_txt, texto, va="center", ha="left",
                    fontsize=9, fontweight="bold", color=cor_txt)
            max_label_x = max(max_label_x, x_txt)

        ax.set_xlim(left=0, right=max_label_x * 1.20)
        ax.tick_params(axis="x", rotation=30, labelsize=8)

        plt.tight_layout()
        caminho = self.output_folder / nome_arquivo
        plt.savefig(caminho, dpi=300, bbox_inches="tight")
        plt.close(fig)
        return caminho
