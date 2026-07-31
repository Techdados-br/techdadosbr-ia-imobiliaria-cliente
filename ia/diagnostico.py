# ia/diagnostico.py

import re
import unicodedata


def limpar_texto(texto):

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = texto.encode(
        "ASCII",
        "ignore"
    ).decode(
        "ASCII"
    )

    return texto.upper()


def converter_numero(valor):

    valor = str(valor)

    valor = valor.replace(".", "")
    valor = valor.replace(",", ".")

    try:
        return float(valor)

    except:
        return 0.0


def buscar_receita(texto):

    texto = limpar_texto(texto)

    padroes = [

        r"TOTAL DE RECEITAS\s*([\d\.,]+)",

        r"TOTAL RECEITAS\s*([\d\.,]+)",

        r"COMPOSICAO RECEITAS ORDINARIAS.*?TOTAL\s*([\d\.,]+)"
    ]

    for padrao in padroes:

        resultado = re.search(
            padrao,
            texto,
            re.DOTALL
        )

        if resultado:

            return converter_numero(
                resultado.group(1)
            )

    return 0.0

def buscar_despesa(texto):

    texto = limpar_texto(texto)

    padroes = [

        r"TOTAL DE DESPESAS\s*([\d\.,]+)",

        r"TOTAL DESPESAS\s*([\d\.,]+)",

        r"COMPOSICAO DESPESAS ORDINARIA.*?TOTAL\s*\-?\s*([\d\.,]+)"
    ]

    for padrao in padroes:

        resultado = re.search(
            padrao,
            texto,
            re.DOTALL
        )

        if resultado:

            return converter_numero(
                resultado.group(1)
            )

    return 0.0


def buscar_inadimplencia(texto):

    texto = limpar_texto(texto)

    padroes = [

        r"UNIDADES INADIMPLENTES.*?([\d\.,]+)$",

        r"TOTAL GERAL DE DEVEDORES\s*([\d\.,]+)"
    ]

    for padrao in padroes:

        resultado = re.search(
            padrao,
            texto,
            re.DOTALL | re.MULTILINE
        )

        if resultado:

            return converter_numero(
                resultado.group(1)
            )

    return 0.0

def calcular_saldo(
    receita,
    despesa
):

        return receita - despesa