import plotly.graph_objects as go


def grafico_receita_despesa(receita, despesa):

    fig = go.Figure()

    fig.add_bar(
        name="Receita",
        y=["Receita"],
        x=[receita],
        orientation="h"
    )

    fig.add_bar(
        name="Despesa",
        y=["Despesa"],
        x=[despesa],
        orientation="h"
    )

    fig.update_layout(
        template="plotly_dark",
        height=280,
        barmode="group",
        showlegend=False
    )

    return fig


def grafico_top_despesas(despesas):

    nomes = [x[0] for x in despesas]
    valores = [x[1] for x in despesas]

    fig = go.Figure()

    fig.add_bar(
        y=nomes,
        x=valores,
        orientation="h"
    )

    fig.update_layout(
        template="plotly_dark",
        title="Top 5 Despesas",
        height=350,
        showlegend=False,
        yaxis=dict(
            autorange="reversed"
        )
    )

    return fig


def grafico_receita_despesa_projecao(dados):

    meses = [x["Mês"] for x in dados]

    receitas = [x["Receita"] for x in dados]

    despesas = [x["Despesa"] for x in dados]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=meses,
            y=receitas,
            mode="lines+markers+text",
            name="Receita",
            text=[
                f"R$ {v:,.0f}"
                for v in receitas
            ],
            textposition="top center"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=meses,
            y=despesas,
            mode="lines+markers+text",
            name="Despesa",
            text=[
                f"R$ {v:,.0f}"
                for v in despesas
            ],
            textposition="top center"
        )
    )

    fig.update_layout(
        title="Receita x Despesa Projetada",
        template="plotly_dark",
        height=300,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            y=1.10
        )
    )

    return fig


def grafico_resultado_projecao(dados):

    meses = [x["Mês"] for x in dados]

    resultados = [x["Resultado"] for x in dados]

    fig = go.Figure()

    fig.add_bar(
        x=meses,
        y=resultados,
        text=[
            f"R$ {v:,.0f}"
            for v in resultados
        ],
        textposition="outside"
    )

    fig.update_layout(
        title="Resultado Projetado",
        template="plotly_dark",
        height=250,
        showlegend=False
    )

    return fig


def gauge_score(score):

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={
                "text": "Score Financeiro"
            },
            gauge={
                "axis": {
                    "range": [0, 100]
                }
            }
        )
    )

    fig.update_layout(
        template="plotly_dark",
        height=280
    )

    return fig


def gauge_inadimplencia(
    receita,
    inadimplencia
):

    percentual = 0

    if receita > 0:

        percentual = (
            inadimplencia / receita
        ) * 100

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=percentual,
            number={
                "suffix": "%"
            },
            title={
                "text": "Inadimplência"
            },
            gauge={
                "axis": {
                    "range": [0, 100]
                }
            }
        )
    )

    fig.update_layout(
        template="plotly_dark",
        height=280
    )

    return fig