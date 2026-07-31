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


def receita_total(df_contratos):

    return float(
        df_contratos["Valor_Mensal"].sum()
    )


def inadimplencia_total(df_inadimplencia):

    return float(
        df_inadimplencia["Valor_Atrasado"].sum()
    )


def contratos_ativos(df_contratos):

    return len(
        df_contratos[
            df_contratos["Status"]
            .astype(str)
            .str.upper()
            == "ATIVO"
        ]
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
        data_fim <= hoje + pd.Timedelta(days=dias)
    )

    return int(
        vencendo.sum()
    )
def receita_perdida_vacancia(
    df_imoveis
):

    vagos = df_imoveis[
        df_imoveis["status"]
        .astype(str)
        .str.upper()
        == "VAGO"
    ]

    return float(
        vagos["valor_aluguel"].sum()
    )
def percentual_inadimplencia(
    receita,
    inadimplencia
):

    if receita <= 0:
        return 0

    return round(
        (inadimplencia / receita) * 100,
        2
    )
def eficiencia_ocupacao(
    ocupados,
    total
):

    if total <= 0:
        return 0

    return round(
        (ocupados / total) * 100,
        2
    )
