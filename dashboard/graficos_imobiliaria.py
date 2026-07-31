import plotly.express as px


def grafico_receita_bairro(df):

    fig = px.bar(
        df.head(10),
        x="valor_aluguel",
        y="bairro",
        orientation="h",
        title="Receita por Bairro"
    )

    return fig


def grafico_ranking_corretores(df):

    fig = px.bar(
        df.head(10),
        x="valor_aluguel",
        y="corretor",
        orientation="h",
        title="Ranking de Corretores"
    )

    return fig


def grafico_status_imoveis(
    ocupados,
    vagos
):

    fig = px.pie(
        names=[
            "Ocupados",
            "Vagos"
        ],
        values=[
            ocupados,
            vagos
        ],
        hole=0.6,
        title="Status dos Imóveis"
    )

    return fig


def grafico_top_inadimplentes(df_inadimplencia):

    top = (
        df_inadimplencia
        .sort_values(
            by="Valor_Atrasado",
            ascending=False
        )
        .head(10)
    )

    fig = px.bar(
        top,
        x="Cliente",
        y="Valor_Atrasado",
        title="Top 10 Inadimplentes"
    )

    return fig


def grafico_inadimplencia_bairro(df_inadimplencia):

    dados = (
        df_inadimplencia
        .groupby("Bairro")["Valor_Atrasado"]
        .sum()
        .reset_index()
        .sort_values(
            by="Valor_Atrasado",
            ascending=False
        )
    )

    fig = px.bar(
        dados,
        x="Bairro",
        y="Valor_Atrasado",
        title="Inadimplência por Bairro"
    )

    return fig