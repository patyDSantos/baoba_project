import ipywidgets as widgets
from IPython.display import display, clear_output
import pandas as pd

__all__ = [
    "cria_dropdown_filtrador",
    "exibe_dropdown_filtrador",
]


def cria_dropdown_filtrador(
    df: pd.DataFrame,
    coluna_dropdown: str,
    coluna_sort: str | None = None,
    linhas: int = 5,
    descricao: str | None = None,
    ordenar_dropdown: bool = False,
):
    """Cria um widget *Dropdown* ligado a um *DataFrame*.

    Quando o usuário seleciona um valor no dropdown, o DataFrame é filtrado
    por esse valor e exibido em ordem decrescente da coluna ``coluna_sort``.

    Parameters
    ----------
    df
        *DataFrame* de origem.
    coluna_dropdown
        Coluna usada para popular o dropdown e filtrar o *DataFrame*.
    coluna_sort, opcional
        Coluna usada para ordenar o *DataFrame* filtrado (ordem decrescente).
        Se ``None``, não aplica ordenação.
    linhas
        Quantidade de linhas exibidas (``head``) do *DataFrame* filtrado.
    descricao, opcional
        Texto exibido ao lado do widget; por padrão usa ``coluna_dropdown``.
    ordenar_dropdown
        Se ``True``, ordena as opções do dropdown alfabeticamente.

    Returns
    -------
    tuple
        ``(dropdown_widget, output_widget)`` prontos para uso.

    Examples
    --------
    >>> dropdown, out = cria_dropdown_filtrador(
    ...     df, "monitoramento_nome.keyword", "interacoes", linhas=10
    ... )
    >>> display(dropdown, out)
    """

    # Valida colunas
    if coluna_dropdown not in df.columns:
        raise ValueError(
            f"A coluna_dropdown '{coluna_dropdown}' não existe no DataFrame."
        )
    if coluna_sort and coluna_sort not in df.columns:
        raise ValueError(
            f"A coluna_sort '{coluna_sort}' não existe no DataFrame."
        )

    # Prepara opções do dropdown
    options = df[coluna_dropdown].dropna().unique().tolist()
    if ordenar_dropdown:
        options = sorted(options)

    dropdown = widgets.Dropdown(options=options, description=descricao or coluna_dropdown)
    out = widgets.Output()

    def _atualiza_display(change):
        if change["type"] == "change" and change["name"] == "value":
            with out:
                clear_output(wait=True)
                valor = change["new"]
                df_filtrado = df[df[coluna_dropdown] == valor]
                if coluna_sort:
                    df_filtrado = df_filtrado.sort_values(by=coluna_sort, ascending=False)
                display(df_filtrado.head(linhas))

    dropdown.observe(_atualiza_display, names="value")
    return dropdown, out


def exibe_dropdown_filtrador(*args, **kwargs):
    """Atalho que cria e já exibe o dropdown com a área de saída."""
    dropdown, out = cria_dropdown_filtrador(*args, **kwargs)
    display(dropdown, out)
    return dropdown, out