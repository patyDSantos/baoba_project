import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.ticker import FuncFormatter
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator

class ProcessamentoMetricasPorMonitoramento:
    
    def __init__(self, df, monitoramentos):
        self.df = df  
        self.monitoramentos = monitoramentos
        self.categorias_cores = {
            "Acessibilidade e Inclusão PCD": "#17becf",
            "Combate à Violência Contra a Mulher": "#ff7f0e",
            "Direitos das Crianças e Adolescentes": "#2ca02c",
            "Igualdade Racial": "#d62728",
            "Igualdade de Gênero": "#9467bd",
            "Patrimônio Público e Probidade Administrativa": "#8c564b",
            "Políticas Públicas": "#1f77b4",
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
    
    @staticmethod
    def formata_numeros_pt_br_tick(x, pos):
        """
        Função para formatação de ticks (duas variáveis, necessária para o FuncFormatter).
        """
        formatted = "{:,.0f}".format(x)
        formatted = formatted.replace(",", ".")
        return formatted

    def formata_numero_simples(self, x):
        """Formata um número sem precisar do parâmetro pos."""
        return self.formata_numeros_pt_br_tick(x, 0)

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
        
    def plota_grafico_ocorrencias_por_monitoramento(self, df, monitoramento, annotations, 
                                       date_column='data', 
                                       date_format='%d-%m-%Y', 
                                       title='Pico de Ocorrências - ',
                                       line_color=None,
                                       save_path=None):


        """
        Filtra o DataFrame pelo monitoramento informado, converte a coluna de datas para datetime,
        agrupa as ocorrências diárias e plota um gráfico de linha com anotações, utilizando a cor
        definida em self.categorias_cores para o monitoramento ou uma cor passada como parâmetro.

        Parâmetros:
          - monitoramento: Nome do monitoramento a ser filtrado (valor da coluna 'monitoramento_nome.keyword').
          - annotations: Lista de dicionários com anotações. Cada dicionário deve conter:
                "date": data formatada conforme `date_format` (ex.: '14-03-2025' ou '14-03' se remover o ano),
                "text": texto da anotação,
                "xytext": tupla com o deslocamento (x, y) para posicionamento do texto da anotação.
          - date_column: Nome da coluna que contém as datas (padrão: 'data').
          - date_format: Formato para exibir as datas no gráfico (padrão: '%d-%m-%Y'; use '%d-%m' para remover o ano).
          - title: Título do gráfico.
          - line_color: Cor da linha no gráfico. Se None, utiliza o valor em self.categorias_cores.
        """

        # Define a cor da linha a partir do dicionário de cores se não for passada
        if line_color is None:
            line_color = self.categorias_cores.get(monitoramento, 'steelblue')

        # Cria uma cópia do DataFrame e filtra linhas com datas válidas
        df_copy = self.df.copy()
        df_copy = df_copy[pd.to_datetime(df_copy[date_column], errors='coerce').notna()]
        df_copy['Data'] = pd.to_datetime(df_copy[date_column]).dt.date

        # Filtra apenas os registros do monitoramento informado
        df_filtered = df_copy[df_copy['monitoramento_nome.keyword'] == monitoramento]

        # Agrupa as ocorrências diárias e renomeia a coluna de contagem para 'Total'
        df_grouped = df_filtered.groupby('Data').size().reset_index(name='Total')
        
        # Cria uma coluna com a data formatada para exibição no eixo x
        df_grouped['Data_str'] = pd.to_datetime(df_grouped['Data']).dt.strftime(date_format)

        # Cria a figura e o eixo para o gráfico de linha
        fig, ax = plt.subplots(figsize=(24, 16))
        ax.plot(df_grouped['Data_str'], df_grouped['Total'], marker='o', 
                linestyle='-', linewidth=3, color=line_color)

        # Configurações de título e rótulos
        ax.set_title(title, fontsize=48)
        ax.set_xlabel('Data', fontsize=36)
        ax.set_ylabel('Ocorrências', fontsize=36)
        ax.tick_params(axis='x', rotation=45, labelsize=24)
        ax.tick_params(axis='y', labelsize=28)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_ylim(0, df_grouped['Total'].max() * 1.2)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=30))  # Tenta limitar a 30 rótulos

        # Insere as anotações para os pontos específicos de acordo com a data informada
        for annotation in annotations:
            matching = df_grouped[df_grouped['Data_str'] == annotation["date"]]
            if not matching.empty:
                y_value = matching['Total'].values[0]
                ax.annotate(
                    annotation["text"],
                    xy=(annotation["date"], y_value),
                    xycoords='data',
                    xytext=annotation["xytext"],
                    textcoords='offset points',
                    fontsize=24,
                    ha='center',
                    arrowprops=dict(
                        arrowstyle='->',
                        color='black',
                        lw=2
                    )
                )

        plt.tight_layout()
        
        # Opcionalmente salvar o gráfico
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')        
        plt.show()
        plt.close()
        
    def plota_grafico_interacoes_por_monitoramento(self, df, monitoramento, annotations, 
                                    date_column='data', 
                                    date_format='%d-%m-%Y', 
                                    title='Pico de Interações - ',
                                    line_color=None,
                                    save_path=None):


        """
        Filtra o DataFrame pelo monitoramento informado, converte a coluna de datas para datetime,
        agrupa as interações diárias e plota um gráfico de linha com anotações, utilizando a cor
        definida em self.categorias_cores para o monitoramento ou uma cor passada como parâmetro.
        
        Além disso, formata os números do eixo Y para o padrão pt-BR e garante escala linear.

        Parâmetros:
          - monitoramento: Nome do monitoramento a ser filtrado (valor da coluna 'monitoramento_nome.keyword').
          - annotations: Lista de dicionários com anotações. Cada dicionário deve conter:
                "date": data formatada conforme `date_format` (ex.: '14-03-2025' ou '14-03' se remover o ano),
                "text": texto da anotação,
                "xytext": tupla com o deslocamento (x, y) para o posicionamento do texto.
          - date_column: Nome da coluna que contém as datas (padrão: 'data').
          - date_format: Formato para exibir as datas no gráfico (padrão: '%d-%m-%Y'; utilize '%d-%m' se não quiser o ano).
          - title: Título do gráfico.
          - line_color: Cor da linha no gráfico. Se None, utiliza self.categorias_cores para o monitoramento.
        """
        
        # Define a cor da linha a partir do dicionário se o parâmetro não for informado
        if line_color is None:
            line_color = self.categorias_cores.get(monitoramento, 'steelblue')

        # Cria uma cópia do DataFrame e filtra linhas com datas válidas
        df_copy = self.df.copy()
        df_copy = df_copy[pd.to_datetime(df_copy[date_column], errors='coerce').notna()]
        df_copy['Data'] = pd.to_datetime(df_copy[date_column]).dt.date

        # Filtra apenas os registros do monitoramento informado
        df_filtered = df_copy[df_copy['monitoramento_nome.keyword'] == monitoramento]

        # Agrupa as interações diárias e renomeia a coluna de contagem para 'Total'
        df_grouped = df_filtered.groupby('Data')['interacoes'].sum().reset_index(name='Total')

        # Cria uma coluna com a data formatada para exibição no eixo x
        df_grouped['Data_str'] = pd.to_datetime(df_grouped['Data']).dt.strftime(date_format)

        # Cria a figura e o eixo para o gráfico de linha
        fig, ax = plt.subplots(figsize=(24, 16))
        ax.plot(df_grouped['Data_str'], df_grouped['Total'], marker='o', 
                linestyle='-', linewidth=3, color=line_color)

        # Configurações de título e rótulos
        ax.set_title(title, fontsize=48)
        ax.set_xlabel('Data', fontsize=36)
        ax.set_ylabel('Interações', fontsize=36)
        ax.tick_params(axis='x', rotation=45, labelsize=24)
        ax.tick_params(axis='y', labelsize=28)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_ylim(0, df_grouped['Total'].max() * 1.2)
        ax.set_yscale('linear')  # Garante escala linear
        ax.xaxis.set_major_locator(MaxNLocator(nbins=30))  # Tenta limitar a 30 rótulos

        ax.yaxis.set_major_formatter(FuncFormatter(self.formata_numeros_pt_br))

        # Insere as anotações para os pontos específicos de acordo com a data informada
        for annotation in annotations:
            matching = df_grouped[df_grouped['Data_str'] == annotation["date"]]
            if not matching.empty:
                y_value = matching['Total'].values[0]
                ax.annotate(
                    annotation["text"],
                    xy=(annotation["date"], y_value),
                    xycoords='data',
                    xytext=annotation["xytext"],
                    textcoords='offset points',
                    fontsize=24,
                    ha='center',
                    arrowprops=dict(
                        arrowstyle='->',
                        color='black',
                        lw=2
                    )
                )

        plt.tight_layout()
        
        # Opcionalmente salvar o gráfico
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')        
        plt.show()
        plt.close()
        
    def plota_grafico_interacoes_por_servico_por_monitoramento(self, df, monitoramento, service_column, title='', save_path=None):
        """
        Filtra o DataFrame pelo monitoramento informado e agrupa as interações por serviço 
        (utilizando a coluna definida em service_column). Plota um gráfico de barras horizontal com a soma das interações 
        para cada serviço, utilizando cores fixas para plataformas específicas e exibindo os valores 
        fora da barra, formatados no padrão pt-BR (ex.: 1.234.567).
        
        Parâmetros:
          - monitoramento: Nome do monitoramento (valor da coluna 'monitoramento_nome.keyword').
          - service_column: Nome da coluna que contém o serviço (ex.: 'servico.keyword').
          - title: Título do gráfico.
        """
       
        df_filtrado = self.df[self.df['monitoramento_nome.keyword'] == monitoramento]
        
        df_servico = (
            df_filtrado
            .groupby(service_column)['interacoes']
            .sum()
            .reset_index(name='Total')
        )
        df_servico = df_servico.sort_values(by='Total', ascending=True).reset_index(drop=True)
        
        # Mapeamento de cores fixas para as plataformas
        platform_colors = {
            "X": "#00acee",                           
            "Instagram - Posts Públicos": "#8a3ab9",
            "Facebook - Posts Públicos": "#1877F2",
            "YouTube - Vídeos": "#e62117"
        }
        
        # Define as cores para cada serviço, utilizando a cor do mapeamento se disponível
        colors = [platform_colors.get(s, 'steelblue') for s in df_servico[service_column]]
        
        # Cria o gráfico de barras horizontal
        plt.figure(figsize=(12, 8))
        plt.barh(df_servico[service_column], df_servico['Total'], color=colors)
        
        plt.title(title, fontsize=20)
        plt.xlabel('Interações', fontsize=16)
        plt.ylabel('Plataforma', fontsize=16)
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        
        max_total = df_servico['Total'].max()
        plt.xlim(0, max_total * 1.2)
        
        offset = max_total * 0.01
        
        # Exibe os valores formatados fora das barras
        for i, row in df_servico.iterrows():
            valor_formatado = self.formata_numero_simples(row['Total'])
            x_text = row['Total'] + offset
            plt.text(x_text, i, valor_formatado, va='center', ha='left', fontsize=12)
        
        ax = plt.gca()
        ax.ticklabel_format(style='plain', axis='x')
        ax.xaxis.set_major_formatter(FuncFormatter(self.formata_numeros_pt_br))
        
        plt.tight_layout()
        
        # Opcionalmente salvar o gráfico
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')        
        plt.show()
        plt.close()
