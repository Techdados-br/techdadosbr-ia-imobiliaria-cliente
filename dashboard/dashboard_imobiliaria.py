import pandas as pd

def calcular_vacancia(df_imoveis):

total = len(df_imoveis)

vagos = len(
    df_imoveis[
        df_imoveis["status"].astype(str).str.upper()
        == "VAGO"
    ]
)

if total == 0:
    return 0

return round(
    (vagos / total) * 100,
    2
)

def imoveis_vagos(df_imoveis):

return len(
    df_imoveis[
        df_imoveis["status"].astype(str).str.upper()
        == "VAGO"
    ]
)

def imoveis_ocupados(df_imoveis):

return len(
    df_imoveis[
        df_imoveis["status"].astype(str).str.upper()
        == "OCUPADO"
    ]
)

def receita_aluguel(df_imoveis):

return float(
    df_imoveis["valor_aluguel"].sum()
)

def ticket_medio(df_imoveis):

return float(
    df_imoveis["valor_aluguel"].mean()
)

def receita_por_bairro(df_imoveis):

return (
    df_imoveis
    .groupby("bairro")["valor_aluguel"]
    .sum()
    .reset_index()
    .sort_values(
        by="valor_aluguel",
        ascending=False
    )
)

def ranking_corretores(df_imoveis):

return (
    df_imoveis
    .groupby("corretor")["valor_aluguel"]
    .sum()
    .reset_index()
    .sort_values(
        by="valor_aluguel",
        ascending=False
    )
)

def gerar_diagnostico_imobiliario(df_imoveis):

diagnostico = []

vacancia = calcular_vacancia(
    df_imoveis
)

if vacancia > 15:

    diagnostico.append(
        "Vacância acima do recomendado."
    )

elif vacancia > 10:

    diagnostico.append(
        "Vacância em nível de atenção."
    )

else:

    diagnostico.append(
        "Vacância sob controle."
    )

return diagnostico

def gerar_insights_imobiliarios(df_imoveis):

insights = []

vacancia = calcular_vacancia(
    df_imoveis
)

receita_bairro = receita_por_bairro(
    df_imoveis
)

if len(receita_bairro) > 0:

    bairro_top = receita_bairro.iloc[0]["bairro"]

    insights.append(
        f"Bairro com maior receita: {bairro_top}."
    )

insights.append(
    f"Taxa de vacância atual: {vacancia}%."
)

insights.append(
    "Monitorar imóveis vagos para aumentar rentabilidade."
)

return insights
import plotly.express as px


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
        .head(10)
    )

    fig = px.bar(
        dados,
        y="Bairro",
        x="Valor_Atrasado",
        orientation="h",
        title="Top 10 Bairros com Maior Inadimplência",
        text="Valor_Atrasado"
    )

    fig.update_layout(
        height=450,
        yaxis_title="",
        xaxis_title="Valor em Atraso (R$)",
        showlegend=False
    )

    fig.update_traces(
        texttemplate="R$ %{x:,.0f}",
        textposition="outside"
    )

    return fig