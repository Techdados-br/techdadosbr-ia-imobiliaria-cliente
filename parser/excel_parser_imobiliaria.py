import pandas as pd


def carregar_abas_imobiliaria(arquivo):

    planilhas = pd.read_excel(
        arquivo,
        sheet_name=None
    )

    return planilhas


def obter_imoveis(planilhas):

    for nome, df in planilhas.items():

        nome_aba = nome.lower()

        if (
            "imovel" in nome_aba
            or "imoveis" in nome_aba
            or "imóveis" in nome_aba
        ):

            return df

    return pd.DataFrame()

def obter_contratos(planilhas):

    for nome, df in planilhas.items():

        if "contrato" in nome.lower():

            return df

    return pd.DataFrame()


def obter_receitas(planilhas):

    for nome, df in planilhas.items():

        if "receita" in nome.lower():

            return df

    return pd.DataFrame()


def obter_inadimplencia(planilhas):

    for nome, df in planilhas.items():

        if (
            "inad" in nome.lower()
            or
            "devedor" in nome.lower()
        ):

            return df

    return pd.DataFrame()


def identificar_tipo_empresa(arquivo):

    try:

        planilhas = pd.read_excel(
            arquivo,
            sheet_name=None
        )

        abas = " ".join(
            planilhas.keys()
        ).lower()

        if (
            "imoveis" in abas
            or
            "contratos" in abas
            or
            "receitas" in abas
        ):

            return "imobiliaria"

    except:

        pass

    return "condominio"