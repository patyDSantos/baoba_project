import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.ticker import FuncFormatter
import matplotlib.dates as mdates

class ProcessamentoMetricas:
    
    def __init__(self, df, monitoramentos):
        self.df = df  
        self.monitoramentos = monitoramentos
        self.categorias_cores = {
            "Acessibilidade e Inclusão PCD": "#1f77b4",
            "Combate à Violência Contra a Mulher": "#ff7f0e",
            "Direitos das Crianças e Adolescentes": "#2ca02c",
            "Igualdade Racial": "#d62728",
            "Igualdade de Gênero": "#9467bd",
            "Patrimônio Público e Probidade Administrativa": "#8c564b",
            "Políticas Públicas": "#bcbd22",
            "Proteção e Inclusão Vulneráveis": "#7f7f7f",
            "Trabalhadores em Plataformas Digitais": "#e377c2",
        }
   
    @staticmethod
    def extrai_metricas(dados, keys):
        """
        Extrai as métricas especificadas na lista keys do campo 'dados',
        que pode ser uma string JSON ou um dicionário.
        Retorna um dicionário com os valores inteiros para cada chave.
        """
        if isinstance(dados, str):
            try:
                dados_dict = json.loads(dados)
            except (json.JSONDecodeError, ValueError):
                return {k: 0 for k in keys}
        elif isinstance(dados, dict):
            dados_dict = dados
        else:
            return {k: 0 for k in keys}
        return {k: int(dados_dict.get(k, 0)) for k in keys}

    @staticmethod
    def formata_numeros_pt_br(x, pos):
        """
        Formata o valor x usando o padrão pt-BR:
        separador de milhares como ponto e sem casas decimais.
        """
        # Formata o número com separador de milhares em estilo US (vírgula) e sem decimais
        formatted = "{:,.0f}".format(x)
        formatted = formatted.replace(",", ".")
        return formatted

    def calcula_interacoes(self, df, service, keys, service_col='servico.keyword'):
        """
        Filtra o DataFrame para o serviço especificado usando a coluna definida por 'service_col',
        extrai as métricas definidas em keys a partir da coluna 'manifestacoes_detalhadas.keyword'
        e cria a coluna 'interacoes_calculadas' com a soma dessas métricas.
        Retorna o DataFrame processado.

        Parâmetros:
        - df: DataFrame de entrada.
        - service: Valor utilizado para filtrar o serviço.
        - keys: Lista com as chaves das métricas a serem extraídas.
        - service_col: Nome da coluna que contém os serviços (padrão 'servico.keyword').
        """
        df_service = df[df[service_col] == service].copy()
        
        df_service['temp_metrics'] = df_service['manifestacoes_detalhadas.keyword'].apply(
            lambda x: self.extrai_metricas(x, keys)
        )
        
        for k in keys:
            df_service[k] = df_service['temp_metrics'].apply(lambda metrics: metrics.get(k, 0))
        
        df_service['interacoes_calculadas'] = df_service[keys].sum(axis=1)
        
        df_service.drop(columns='temp_metrics', inplace=True)
        
        return df_service
        
    def plota_grafico_ocorrencias_df(self, df, coluna, title, colors=None, log_scale=False,
                                    annotate=True, figsize=(12,8), fontsize=14):
        """
        Plota um gráfico de barras horizontal com base nos dados agregados de um DataFrame.
        Essa função calcula a contagem de ocorrências da coluna informada, ordena os resultados
        e plota o gráfico com as configurações passadas.
        
        Parâmetros:
        - df: DataFrame de onde os dados serão extraídos.
        - coluna: Nome da coluna para realizar o value_counts.
        - title: Título do gráfico.
        - colors: Cor ou lista de cores para as barras.
        - log_scale: Se True, utiliza escala logarítmica para o eixo X.
        - annotate: Se True, cada barra é anotada com seu valor.
        - figsize: Tamanho da figura.
        - fontsize: Tamanho da fonte para textos e rótulos.
        """
        series = df[coluna].value_counts().sort_values()
        
        plt.figure(figsize=figsize)
        ax = series.plot(kind='barh', color=colors, logx=log_scale)
        
        ax.xaxis.set_major_formatter(FuncFormatter(self.formata_numeros_pt_br))
        
        if annotate:
            x_max = series.max()
            for bar in ax.patches:
                width = bar.get_width()
                # Anota cada barra com seu valor formatado conforme o padrão PT-BR.
                ax.text(width * 1.02, bar.get_y() + bar.get_height() / 2,
                        f'{int(width):,}'.replace(",", "."),
                        va='center', ha='left', fontsize=fontsize)
            if log_scale:
                plt.xlim(right=x_max * 18)
        
        if log_scale:
            plt.xlim(right=x_max * 18)
        else:
            plt.xlim(right=x_max * 1.2)
        
        if log_scale:
            ax.minorticks_off()
            ax.grid(False, which='minor', axis='x')
        
        ax.tick_params(axis='x', which='major', labelsize=14)
        ax.tick_params(axis='y', which='major', labelsize=16)
        
        plt.xlabel('Ocorrências', fontsize=fontsize)
        plt.title(title, fontsize=fontsize + 8)
        plt.ylabel('Monitoramento', fontsize=18)
        plt.tight_layout()
        plt.show()

    def plota_grafico_interacoes(self, df, monitoramento_col, interacoes_col, title, colors=None, 
                                log_scale=False, annotate=True, figsize=(12,8), fontsize=14):
        """
        Plota um gráfico de barras horizontal para as interações somadas por monitoramento.
        
        A função agrupa o DataFrame pela coluna 'monitoramento_col', soma os valores
        da coluna 'interacoes_col' para cada grupo, e plota o resultado. Se 'annotate' for True,
        anota cada barra com o valor correspondente (formatado com separador de milhar).
        Caso 'log_scale' seja True, utiliza escala logarítmica para o eixo X e ajusta os ticks.
        
        Parâmetros:
        - df: DataFrame de onde os dados serão extraídos.
        - monitoramento_col: Nome da coluna a ser utilizada para o agrupamento.
        - interacoes_col: Nome da coluna que contém os valores de interações a serem somados.
        - title: Título do gráfico.
        - colors: Cor ou lista de cores para as barras (padrão: None).
        - log_scale: Se True, usa escala logarítmica para o eixo X (padrão: False).
        - annotate: Se True, anota cada barra com seu valor (padrão: True).
        - figsize: Tamanho da figura (padrão: (12,8)).
        - fontsize: Tamanho da fonte para os textos (padrão: 14).
        """
        series = df.groupby(monitoramento_col)[interacoes_col].sum().sort_values()

        plt.figure(figsize=figsize)
        ax = series.plot(kind='barh', color=colors, logx=log_scale)

        if annotate:
            x_max = series.max()
            for bar in ax.patches:
                width = bar.get_width()
                # Anota cada barra com o valor formatado
                ax.text(width * 1.02, bar.get_y() + bar.get_height() / 2,
                        f'{int(width):,}'.replace(",", "."), va='center', ha='left', fontsize=fontsize)
            if log_scale:
                plt.xlim(right=x_max * 18)

        if log_scale:
            ax.minorticks_off()
            ax.grid(False, which='minor', axis='x')

        ax.tick_params(axis='x', which='major', labelsize=14)
        ax.tick_params(axis='y', which='major', labelsize=14)

        plt.title(title, fontsize=fontsize + 8)
        plt.ylabel('Monitoramento', fontsize=18)
        plt.xlabel('Interações', fontsize=18)
        plt.tight_layout()
        plt.show()
        
    def plota_grid_graficos_interacoes_e_ocorrencias_estilo_linha(
            self, df, top_title, date_col, monitoramento_col, 
            ocorrencia_col, interacoes_col,
            figsize=(16, 10),
            title_fontsize=20, label_fontsize=16, legend_fontsize=14, tick_labelsize=14):
        """
        Converte a coluna de datas para datetime, extrai a data (sem horário),
        agrupa por data e monitoramento, e plota ocorrências e interações diárias
        para cada monitoramento em gráficos de linhas.
        
        Exibe uma única caixa de legenda ao lado direito dos gráficos,
        e utiliza tamanhos maiores para facilitar a leitura.

        Parâmetros:
        - df: DataFrame de entrada.
        - top_title: Título complementar exibido nos gráficos.
        - date_col: Nome da coluna que contém a data.
        - monitoramento_col: Nome da coluna que identifica o monitoramento.
        - ocorrencia_col: Nome da coluna usada para contar ocorrências (utiliza o método 'size').
        - interacoes_col: Nome da coluna que contém os valores de interações a serem somados.
        
        - figsize: Tamanho da figura (largura x altura).
        - title_fontsize: Tamanho de fonte para o título de cada subplot.
        - label_fontsize: Tamanho de fonte para os rótulos dos eixos.
        - legend_fontsize: Tamanho de fonte da legenda.
        - tick_labelsize: Tamanho de fonte das marcações dos eixos (ticks).
        """

        # Copia e converte a coluna de datas
        df_copy = df.copy()
        df_copy['DataDateTime'] = pd.to_datetime(df_copy[date_col], errors='coerce')
        df_copy['DataSomenteDia'] = df_copy['DataDateTime'].dt.date

        # Agrupa por data e monitoramento
        df_grouped = (
            df_copy
            .groupby(['DataSomenteDia', monitoramento_col], as_index=False)
            .agg(Ocorrencias=(ocorrencia_col, 'size'),
                 Interacoes=(interacoes_col, 'sum'))
            .sort_values(by='DataSomenteDia')
        )
        df_grouped['DataSomenteDia'] = pd.to_datetime(df_grouped['DataSomenteDia'])

        # Cria tabelas pivot
        df_occ_pivot = df_grouped.pivot(index='DataSomenteDia', columns=monitoramento_col, values='Ocorrencias').fillna(0)
        df_int_pivot = df_grouped.pivot(index='DataSomenteDia', columns=monitoramento_col, values='Interacoes').fillna(0)

        # Obtém a lista de cores conforme o mapeamento externo
        # Se o atributo não existir, utiliza um mapeamento padrão
        categorias_cores = getattr(self, "categorias_cores", {
            col: "#999999" for col in df_occ_pivot.columns
        })
        cores_linha_ocorrencias = [categorias_cores.get(col, "#999999") for col in df_occ_pivot.columns]
        cores_linha_interacoes   = [categorias_cores.get(col, "#999999") for col in df_int_pivot.columns]

        # Cria os subplots
        fig, axs = plt.subplots(2, 1, figsize=figsize, sharex=True)

        # Gráfico de linhas para Ocorrências
        df_occ_pivot.plot(
            ax=axs[0],
            marker='o',
            legend=False,
            color=cores_linha_ocorrencias
        )
        axs[0].set_title(f'Ocorrências diárias - {top_title}', fontsize=title_fontsize)
        axs[0].set_ylabel('Ocorrências', fontsize=label_fontsize)
        axs[0].tick_params(axis='x', rotation=90, labelsize=tick_labelsize)
        axs[0].tick_params(axis='y', labelsize=tick_labelsize)

        # Gráfico de linhas para Interações
        df_int_pivot.plot(
            ax=axs[1],
            marker='s',
            legend=False,
            color=cores_linha_interacoes
        )
        axs[1].set_title(f'Interações diárias - {top_title}', fontsize=title_fontsize)
        axs[1].set_xlabel('Data', fontsize=label_fontsize)
        axs[1].set_ylabel('Interações', fontsize=label_fontsize)
        axs[1].tick_params(axis='x', rotation=90, labelsize=tick_labelsize)
        axs[1].tick_params(axis='y', labelsize=tick_labelsize)

        # Formata o eixo X para exibir as datas no formato dia-mês
        date_formatter = mdates.DateFormatter('%d-%m')
        axs[0].xaxis.set_major_formatter(date_formatter)
        axs[1].xaxis.set_major_formatter(date_formatter)

        # Ajusta explicitamente os labels do eixo X
        plt.setp(axs[0].get_xticklabels(), fontsize=tick_labelsize)
        plt.setp(axs[1].get_xticklabels(), fontsize=tick_labelsize)

        # Grid somente no eixo X
        for ax in axs:
            ax.grid(True, which='major', axis='x', linestyle='--', linewidth=0.5, color='gray', alpha=0.7)
            ax.grid(False, which='major', axis='y')

        # Legenda única
        handles, labels = axs[0].get_legend_handles_labels()
        plt.tight_layout(rect=[0, 0, 0.8, 1])
        fig.legend(handles, labels,
                   loc='center left',
                   bbox_to_anchor=(0.82, 0.5),
                   fontsize=legend_fontsize)
        plt.show()

    def plota_grid_graficos_interacoes_e_ocorrencias_estilo_area(
            self, df, top_title, date_col, monitoramento_col,
            ocorrencia_col, interacoes_col,
            figsize=(16, 10),
            title_fontsize=20, label_fontsize=16,
            legend_fontsize=14, tick_labelsize=14,
            alpha_value=0.8,
            linewidth=1
    ):
        """
        Converte a coluna de datas para datetime, extrai a data (sem horário),
        agrupa por data e monitoramento, e plota ocorrências e interações diárias
        para cada monitoramento em gráficos de área (não empilhados), usando cores definidas externamente.
        
        Exibe uma única caixa de legenda ao lado direito dos gráficos
        e utiliza tamanhos maiores para facilitar a leitura.
        
        Parâmetros:
        - df: DataFrame de entrada.
        - top_title: Título complementar exibido nos gráficos.
        - date_col: Nome da coluna que contém a data.
        - monitoramento_col: Nome da coluna que identifica o monitoramento.
        - ocorrencia_col: Nome da coluna usada para contar ocorrências (utiliza o método 'size').
        - interacoes_col: Nome da coluna que contém os valores de interações a serem somados.
        
        - figsize: Tamanho da figura (largura x altura).
        - title_fontsize: Tamanho de fonte para o título de cada subplot.
        - label_fontsize: Tamanho de fonte para os rótulos dos eixos.
        - legend_fontsize: Tamanho de fonte da legenda.
        - tick_labelsize: Tamanho de fonte das marcações dos eixos (ticks).
        
        - alpha_value: Transparência das áreas (0 a 1).
        - linewidth: Largura da linha de contorno de cada área.
        """

        # Usa o dicionário de cores externo se existir
        if hasattr(self, "categorias_cores"):
            categorias_cores = self.categorias_cores

        # Copia e converte a coluna de datas
        df_copy = df.copy()
        df_copy['DataDateTime'] = pd.to_datetime(df_copy[date_col], errors='coerce')
        df_copy['DataSomenteDia'] = df_copy['DataDateTime'].dt.date

        # Agrupa por data e monitoramento
        df_grouped = (
            df_copy
            .groupby(['DataSomenteDia', monitoramento_col], as_index=False)
            .agg(Ocorrencias=(ocorrencia_col, 'size'),
                 Interacoes=(interacoes_col, 'sum'))
            .sort_values(by='DataSomenteDia')
        )
        df_grouped['DataSomenteDia'] = pd.to_datetime(df_grouped['DataSomenteDia'])

        # Pivot tables
        df_occ_pivot = df_grouped.pivot(index='DataSomenteDia', columns=monitoramento_col, values='Ocorrencias').fillna(0)
        df_int_pivot = df_grouped.pivot(index='DataSomenteDia', columns=monitoramento_col, values='Interacoes').fillna(0)

        # Gera listas de cores conforme a ordem das colunas
        cores_ocorrencias = [categorias_cores.get(col, "#999999") for col in df_occ_pivot.columns]
        cores_interacoes   = [categorias_cores.get(col, "#999999") for col in df_int_pivot.columns]

        fig, axs = plt.subplots(2, 1, figsize=figsize, sharex=True)

        # Gráfico de área para Ocorrências
        df_occ_pivot.plot.area(
            ax=axs[0],
            legend=False,
            stacked=False,
            alpha=alpha_value,
            color=cores_ocorrencias,
            linewidth=linewidth
        )
        # Ajusta os contornos
        for coll in axs[0].collections:
            coll.set_edgecolor("black")
            coll.set_linewidth(linewidth)

        axs[0].set_title(f'Ocorrências diárias - {top_title}', fontsize=title_fontsize)
        axs[0].set_ylabel('Ocorrências', fontsize=label_fontsize)
        axs[0].tick_params(axis='x', rotation=90, labelsize=tick_labelsize)
        axs[0].tick_params(axis='y', labelsize=tick_labelsize)

        # Gráfico de área para Interações
        df_int_pivot.plot.area(
            ax=axs[1],
            legend=False,
            stacked=False,
            alpha=alpha_value,
            color=cores_interacoes,
            linewidth=linewidth
        )
        for coll in axs[1].collections:
            coll.set_edgecolor("black")
            coll.set_linewidth(linewidth)

        axs[1].set_title(f'Interações diárias - {top_title}', fontsize=title_fontsize)
        axs[1].set_xlabel('Data', fontsize=label_fontsize)
        axs[1].set_ylabel('Interações', fontsize=label_fontsize)
        axs[1].tick_params(axis='x', rotation=90, labelsize=tick_labelsize)
        axs[1].tick_params(axis='y', labelsize=tick_labelsize)

        # Formata o eixo X (dia-mês)
        date_formatter = mdates.DateFormatter('%d-%m')
        axs[0].xaxis.set_major_formatter(date_formatter)
        axs[1].xaxis.set_major_formatter(date_formatter)

        for ax in axs:
            ax.grid(True, which='major', axis='x', linestyle='--', linewidth=0.5, color='gray', alpha=0.7)
            ax.grid(False, which='major', axis='y')

        handles, labels = axs[0].get_legend_handles_labels()
        plt.tight_layout(rect=[0, 0, 0.8, 1])
        fig.legend(handles, labels,
                   loc='center left',
                   bbox_to_anchor=(0.82, 0.5),
                   fontsize=legend_fontsize)
        plt.show()
