import pandas as pd


def contratos_ativos(df_contratos):

    return len(
        df_contratos[
            df_contratos["Status"]
            .astype(str)
            .str.upper()
            == "ATIVO"
        ]
    )


def total_contratos(df_contratos):

    return len(df_contratos)


def valor_medio_contrato(df_contratos):

    return float(
        df_contratos["Valor_Mensal"].mean()
    )


def contratos_vencendo(
    df_contratos,
    dias=30
):

    hoje = pd.Timestamp.today()

    data_fim = pd.to_datetime(
        df_contratos["Data_Fim"],
        errors="coerce"
    )

    vencendo = (
        (data_fim >= hoje)
        &
        (
            data_fim
            <= hoje + pd.Timedelta(days=dias)
        )
    )

    return int(
        vencendo.sum()
    )


def contratos_por_status(df_contratos):

    dados = (
        df_contratos["Status"]
        .astype(str)
        .value_counts()
        .reset_index()
    )

    dados.columns = [
        "Status",
        "Quantidade"
    ]

    return dados


def top_contratos_valor(df_contratos):

    return (
        df_contratos
        .sort_values(
            by="Valor_Mensal",
            ascending=False
        )
        .head(10)
    )


def contratos_vencendo_df(
    df_contratos,
    dias=30
):

    hoje = pd.Timestamp.today()

    df = df_contratos.copy()

    df["Data_Fim"] = pd.to_datetime(
        df["Data_Fim"],
        errors="coerce"
    )

    return df[
        (df["Data_Fim"] >= hoje)
        &
        (
            df["Data_Fim"]
            <= hoje + pd.Timedelta(days=dias)
        )
    ]


def gerar_alertas_contratos(
    df_contratos
):

    alertas = []

    vencendo = contratos_vencendo(
        df_contratos
    )

    if vencendo > 0:

        alertas.append(
            f"{vencendo} contratos vencem nos próximos 30 dias."
        )

    if vencendo > 10:

        alertas.append(
            "Necessário iniciar campanha de renovação."
        )

    if len(alertas) == 0:

        alertas.append(
            "Nenhum alerta contratual encontrado."
        )

    return alertas