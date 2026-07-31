import pandas as pd


MAPA_COLUNAS = {

    "status": [
        "status",
        "situação",
        "situacao",
        "ocupacao",
        "ocupação"
    ],

    "bairro": [
        "bairro",
        "regiao",
        "região",
        "localizacao",
        "localização"
    ],

    "corretor": [
        "corretor",
        "consultor",
        "responsavel",
        "responsável",
        "captador"
    ],

    "valor_aluguel": [
        "valor_aluguel",
        "aluguel",
        "valor mensal",
        "valor_mensal",
        "receita locacao",
        "receita_locacao"
    ]
}


def normalizar_colunas(df):

    novo_nome = {}

    for coluna in df.columns:

        coluna_limpa = (
            str(coluna)
            .strip()
            .lower()
        )

        for destino, aliases in MAPA_COLUNAS.items():

            if coluna_limpa in aliases:

                novo_nome[coluna] = destino

    return df.rename(
        columns=novo_nome
    )


def validar_imoveis(df):

    obrigatorias = [
        "status",
        "bairro",
        "corretor",
        "valor_aluguel"
    ]

    faltando = []

    for coluna in obrigatorias:

        if coluna not in df.columns:

            faltando.append(coluna)

    return faltando