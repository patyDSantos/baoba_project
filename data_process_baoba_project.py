import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

class MetricsProcessor:
    @staticmethod
    def extract_metrics(dados, keys):
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

    def process_service(self, df, service, keys):
        """
        Filtra o DataFrame para o serviço especificado,
        extrai as métricas definidas em keys a partir da coluna 'manifestacoes_detalhadas.keyword'
        e cria a coluna 'interacoes_calculadas' com a soma dessas métricas.
        Retorna o DataFrame processado.
        """
        df_service = df[df['servico.keyword'] == service].copy()
        for k in keys:
            df_service[k] = df_service['manifestacoes_detalhadas.keyword'].apply(
                lambda x: MetricsProcessor.extract_metrics(x, keys)[k]
            )
        df_service['interacoes_calculadas'] = df_service[keys].sum(axis=1)
        return df_service

    def plot_daily_metrics(self, df, monitoramento, top_title):
        """
        Converte a coluna de data, filtra para o monitoramento informado,
        agrupa por data (dia) e plota ocorrências e interações diárias.
        """
        df_copy = df.copy()

        df_copy['DataDateTime'] = pd.to_datetime(df_copy['data'])
        df_copy['DataSomenteDia'] = df_copy['DataDateTime'].dt.date

        df_filtro = df_copy[df_copy['monitoramento_nome.keyword'] == monitoramento]

        df_agrupado = (
            df_filtro
            .groupby('DataSomenteDia', as_index=False)
            .agg(Ocorrencias=('conteudo.keyword', 'size'),
                 Interacoes=('interacoes', 'sum'))
            .sort_values(by='DataSomenteDia')
        )

        df_agrupado['DataLabel'] = pd.to_datetime(df_agrupado['DataSomenteDia']).dt.strftime('%d-%m')

        fig, axs = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

        # Plot das ocorrências
        axs[0].plot(df_agrupado['DataLabel'], df_agrupado['Ocorrencias'],
                    marker='o', color='steelblue', linewidth=2)
        axs[0].set_title(f'Ocorrências diárias - {top_title}', fontsize=16)
        axs[0].set_ylabel('Ocorrências', fontsize=14)
        axs[0].tick_params(axis='x', rotation=90)

        # Plot das interações
        axs[1].plot(df_agrupado['DataLabel'], df_agrupado['Interacoes'],
                    marker='s', color='coral', linewidth=2)
        axs[1].set_title(f'Interações diárias - {top_title}', fontsize=16)
        axs[1].set_xlabel('Data', fontsize=14)
        axs[1].set_ylabel('Interações', fontsize=14)

        # Adiciona apenas linhas verticais (grid somente no eixo x)
        for ax in axs:
            ax.grid(True, which='major', axis='x', linestyle='--', linewidth=0.5, color='gray', alpha=0.7)
            # Desabilita a grid horizontal se não for necessária
            ax.grid(False, which='major', axis='y')

        plt.tight_layout()
        plt.show()

    def plot_daily_occurrences(self, df, monitoramento, annotations, 
                           date_column='data', 
                           date_format='%d-%m-%Y', 
                           title='Pico de Ocorrências - Desinformação em Políticas Públicas'):
        """
        Filtra o DataFrame pelo monitoramento informado, converte a coluna de data para datetime,
        agrupa as ocorrências diárias e plota um gráfico de linha com anotações.
    
        Parâmetros:
          - df: DataFrame contendo os dados.
          - monitoramento: Nome do monitoramento a ser filtrado (valor da coluna 'monitoramento_nome.keyword').
          - annotations: Lista de dicionários com anotações. Cada dicionário deve ter as chaves:
                "date": data no formato especificado em `date_format` (ex.: '14-03-2025' ou '14-03' se remover o ano),
                "text": texto da anotação,
                "xytext": tupla com o deslocamento (x, y) para a anotação.
          - date_column: Nome da coluna que contém as datas (padrão: 'Data de Ocorrência').
          - date_format: Formato para exibir a data no gráfico (padrão: '%d-%m-%Y'; use '%d-%m' para remover o ano).
          - title: Título do gráfico.
        """
        df = df[pd.to_datetime(df[date_column], errors='coerce').notna()]
        
        df['Data'] = pd.to_datetime(df[date_column]).dt.date
        
        df = df[df['monitoramento_nome.keyword'] == monitoramento]
        
        df_ocorrencias = df.groupby('Data').size().reset_index(name='Total')
        
        df_ocorrencias['Data'] = pd.to_datetime(df_ocorrencias['Data']).dt.strftime(date_format)
        
        # Criar o gráfico de linha
        plt.figure(figsize=(24, 16))
        plt.plot(df_ocorrencias['Data'], df_ocorrencias['Total'], marker='o', linestyle='-', linewidth=3, color='steelblue')
        
        plt.title(title, fontsize=48)
        plt.ylabel('Total de Ocorrências', fontsize=36)
        plt.xticks(rotation=45, fontsize=24)
        plt.yticks(fontsize=28)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Ajustar o limite superior do eixo Y
        plt.ylim(0, df_ocorrencias['Total'].max() * 1.2)
        
        # Inserir as anotações conforme os picos informados
        for annotation in annotations:
            # Encontrar a linha correspondente à data da anotação
            match_data = df_ocorrencias[df_ocorrencias['Data'] == annotation["date"]]
            if not match_data.empty:
                y_value = match_data['Total'].values[0]
                x_value = annotation["date"]
                
                plt.annotate(
                    annotation["text"],
                    xy=(x_value, y_value),         # Posição do ponto a ser anotado
                    xycoords='data',
                    xytext=annotation["xytext"],     # Deslocamento da anotação
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
        plt.show()

    def plot_daily_interactions(self, df, monitoramento, annotations, 
                            date_column='data', 
                            date_format='%d-%m-%Y', 
                            title='Interações Diárias - Desinformação em Políticas Públicas'):
        """
        Filtra o DataFrame pelo monitoramento informado, converte a coluna de data para datetime,
        agrupa as interações diárias (somando os valores da coluna 'interacoes') e plota um gráfico de linha com anotações.
        
        Parâmetros:
          - df: DataFrame contendo os dados.
          - monitoramento: Nome do monitoramento a ser filtrado (valor da coluna 'monitoramento_nome.keyword').
          - annotations: Lista de dicionários com anotações. Cada dicionário deve ter as chaves:
                "date": data no formato especificado em `date_format` (ex.: '14-03-2025' ou '14-03' se remover o ano),
                "text": texto da anotação,
                "xytext": tupla com o deslocamento (x, y) para a anotação.
          - date_column: Nome da coluna que contém as datas (padrão: 'data').
          - date_format: Formato para exibir a data no gráfico (padrão: '%d-%m-%Y'; use '%d-%m' para remover o ano).
          - title: Título do gráfico.
        """
        df = df[pd.to_datetime(df[date_column], errors='coerce').notna()]
        
        df['Data'] = pd.to_datetime(df[date_column]).dt.date
        
        df = df[df['monitoramento_nome.keyword'] == monitoramento]
        
        df_interacoes = df.groupby('Data')['interacoes'].sum().reset_index(name='Total')
        
        df_interacoes['Data'] = pd.to_datetime(df_interacoes['Data']).dt.strftime(date_format)
        
        # Criar o gráfico de linha
        plt.figure(figsize=(24, 16))
        plt.plot(df_interacoes['Data'], df_interacoes['Total'], marker='o', linestyle='-', linewidth=3, color='steelblue')
        
        plt.title(title, fontsize=48)
        plt.ylabel('Total de Interações', fontsize=36)
        plt.xticks(rotation=45, fontsize=24)
        plt.yticks(fontsize=28)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Ajustar o limite superior do eixo Y
        plt.ylim(0, df_interacoes['Total'].max() * 1.2)
        
        # Inserir as anotações conforme os picos informados
        for annotation in annotations:
            # Encontrar a linha correspondente à data da anotação
            match_data = df_interacoes[df_interacoes['Data'] == annotation["date"]]
            if not match_data.empty:
                y_value = match_data['Total'].values[0]
                x_value = annotation["date"]
                
                plt.annotate(
                    annotation["text"],
                    xy=(x_value, y_value),         # Posição do ponto a ser anotado
                    xycoords='data',
                    xytext=annotation["xytext"],     # Deslocamento da anotação
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
        plt.show()

    def plot_interactions_by_service_horizontal(self, df, monitoramento, 
                                            title='Interações por Serviço - ' + monitoramento):
        """
        Filtra o DataFrame pelo monitoramento informado e agrupa as interações por serviço (coluna 'servico.keyword').
        Plota um gráfico de barras horizontal com a soma das interações para cada serviço, 
        fixando as cores para plataformas específicas e exibindo o valor fora da barra.
        """
        # Função para formatar números no padrão brasileiro (ex.: 1234567 -> '1.234.567')
        def format_brazilian(num):
            return f"{int(round(num)):,}".replace(",", ".")
        
        df_filtrado = df[df['monitoramento_nome.keyword'] == monitoramento]
        
        df_servico = df_filtrado.groupby('servico.keyword')['interacoes'].sum().reset_index(name='Total')
        
        df_servico = df_servico.sort_values(by='Total', ascending=True).reset_index(drop=True)
        
        # Mapeamento de cores fixas para as plataformas
        platform_colors = {
            "X": "#00acee",                           
            "Instagram - Posts Públicos": "#8a3ab9",
            "Facebook - Posts Públicos": "#1877F2",
            "YouTube - Vídeos": "#e62117"
        }
        
        # Criar lista de cores para cada serviço, usando a cor fixa se disponível
        colors = [platform_colors.get(s, 'steelblue') for s in df_servico['servico.keyword']]
        
        # Criar o gráfico de barras horizontal
        plt.figure(figsize=(12, 8))
        plt.barh(df_servico['servico.keyword'], df_servico['Total'], color=colors)
        
        plt.title(title, fontsize=20)
        plt.xlabel('Total de Interações', fontsize=16)
        plt.ylabel('Serviço', fontsize=16)
        plt.xticks(fontsize=12)
        plt.yticks(fontsize=12)
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        
        max_total = df_servico['Total'].max()
        
        plt.xlim(0, max_total * 1.2)
        
        offset = max_total * 0.01
        
        for i, row in df_servico.iterrows():
            valor_formatado = format_brazilian(row['Total'])
            x_text = row['Total'] + offset
            plt.text(x_text, i, valor_formatado, va='center', ha='left', fontsize=12)
        
        ax = plt.gca()
        ax.ticklabel_format(style='plain', axis='x')
        
        plt.tight_layout()
        plt.show()
