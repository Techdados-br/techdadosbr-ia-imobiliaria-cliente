def calcular_score(
    vacancia,
    inadimplencia,
    receita,
    contratos_vencendo
):

    score = 100

    # Vacância

    if vacancia > 50:
        score -= 30

    elif vacancia > 35:
        score -= 20

    elif vacancia > 20:
        score -= 10

    # Inadimplência

    percentual_inadimplencia = 0

    if receita > 0:

        percentual_inadimplencia = (
            inadimplencia / receita
        ) * 100

    if percentual_inadimplencia > 50:
        score -= 30

    elif percentual_inadimplencia > 30:
        score -= 20

    elif percentual_inadimplencia > 15:
        score -= 10

    # Contratos vencendo

    if contratos_vencendo > 100:
        score -= 15

    elif contratos_vencendo > 50:
        score -= 10

    if score < 0:
        score = 0

    return round(score)

def gerar_resumo_executivo(
    score,
    classificacao
):

    return [
        f"Score Geral: {score}/100",
        f"Classificação: {classificacao}"
    ]

def classificar_score(score):

    if score >= 90:
        return "🟢 EXCELENTE"

    elif score >= 70:
        return "🟡 BOA"

    elif score >= 50:
        return "🟠 ATENÇÃO"

    else:
        return "🔴 CRÍTICA"