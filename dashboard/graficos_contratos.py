import plotly.express as px


def grafico_contratos_status(df_status):

    fig = px.pie(
        df_status,
        names="Status",
        values="Quantidade",
        hole=0.6,
        title="Contratos por Status"
    )

    return fig


def grafico_top_contratos(df_contratos):

    fig = px.bar(
        df_contratos,
        x="Cliente",
        y="Valor_Mensal",
        title="Top 10 Contratos por Valor"
    )

    fig.update_layout(
        xaxis_title="Cliente",
        yaxis_title="Valor Mensal"
    )

    return fig


def grafico_contratos_vencendo(df_vencendo):

    fig = px.bar(
        df_vencendo,
        x="Cliente",
        y="Valor_Mensal",
        color="Data_Fim",
        title="Contratos Vencendo"
    )

    fig.update_layout(
        xaxis_title="Cliente",
        yaxis_title="Valor Mensal"
    )

    return fig


def grafico_contratos_bairro(df_contratos):

    if "Bairro" not in df_contratos.columns:
        return None

    dados = (
        df_contratos
        .groupby("Bairro")["Valor_Mensal"]
        .sum()
        .reset_index()
        .sort_values(
            by="Valor_Mensal",
            ascending=False
        )
    )

    fig = px.bar(
        dados,
        x="Bairro",
        y="Valor_Mensal",
        title="Contratos por Bairro"
    )

    return fig