import json
import pandas as pd
import matplotlib.pyplot as plt

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