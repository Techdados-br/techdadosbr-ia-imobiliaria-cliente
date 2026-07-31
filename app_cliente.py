import unicodedata
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import textwrap
import re
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)

from parser.excel_parser_imobiliaria import (
    carregar_abas_imobiliaria,
    obter_imoveis,
    obter_contratos,
    obter_receitas,
    obter_inadimplencia
)

from ia.normalizador_imobiliaria import (
    normalizar_colunas,
    validar_imoveis
)

from ia.motor_imobiliaria import (
    calcular_vacancia,
    imoveis_vagos,
    imoveis_ocupados,
    ticket_medio,
    receita_por_bairro,
    ranking_corretores,
    gerar_diagnostico_imobiliario,
    gerar_insights_imobiliarios,
    receita_total,
    inadimplencia_total,
    contratos_ativos,
    contratos_vencendo,
    receita_perdida_vacancia,
    percentual_inadimplencia,
    eficiencia_ocupacao
)

from ia.motor_contratos import (
    total_contratos,
    valor_medio_contrato,
    contratos_por_status,
    top_contratos_valor,
    contratos_vencendo_df,
    gerar_alertas_contratos
)

from ia.score_imobiliaria import (
    calcular_score,
    classificar_score,
    gerar_resumo_executivo
)

from dashboard.cards_imobiliaria import (
    card_imoveis_totais,
    card_imoveis_ocupados,
    card_imoveis_vagos,
    card_vacancia,
    card_ticket_medio,
    card_receita_total,
    card_inadimplencia_imob,
    card_contratos,
    card_contratos_vencendo
)

from dashboard.cards_contratos import (
    card_total_contratos,
    card_contratos_ativos,
    card_contratos_vencendo,
    card_valor_medio_contrato
)

from dashboard.graficos_imobiliaria import (
    grafico_receita_bairro,
    grafico_ranking_corretores,
    grafico_status_imoveis,
    grafico_top_inadimplentes,
    grafico_inadimplencia_bairro
)

from dashboard.graficos_contratos import (
    grafico_contratos_status,
    grafico_top_contratos,
    grafico_contratos_vencendo
)

from dashboard.filtros_globais import aplicar_filtros

from dashboard.pagina_visao_geral import (
    exibir_visao_geral
)

from dashboard.pagina_imoveis import (
    exibir_imoveis
)

from dashboard.pagina_executivo_layout_v5_limpa import (
    exibir_executivo
)

from dashboard.pagina_contratos import (
    exibir_contratos
)

from dashboard.pagina_riscos import (
    exibir_riscos
)

from dashboard.pagina_insights import (
    exibir_insights
)

from dashboard.pagina_dados import (
    exibir_dados
)


# ==================================================
# RELATÓRIO PDF - MÊS ATUAL
# ==================================================

def _moeda_pdf(valor):
    try:
        texto = f"{float(valor):,.2f}"
        texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {texto}"
    except Exception:
        return "R$ 0,00"


def _percentual_pdf(valor):
    try:
        return f"{float(valor):.1f}%".replace(".", ",")
    except Exception:
        return "0,0%"


def _texto_pdf(valor, padrao="Não informado"):
    texto = str(valor or "").strip()
    return texto if texto else padrao


def identificar_periodo_arquivo_imobiliaria(nome_arquivo):
    meses = {
        "janeiro": "Janeiro",
        "jan": "Janeiro",
        "fevereiro": "Fevereiro",
        "fev": "Fevereiro",
        "marco": "Março",
        "mar": "Março",
        "abril": "Abril",
        "abr": "Abril",
        "maio": "Maio",
        "mai": "Maio",
        "junho": "Junho",
        "jun": "Junho",
        "julho": "Julho",
        "jul": "Julho",
        "agosto": "Agosto",
        "ago": "Agosto",
        "setembro": "Setembro",
        "set": "Setembro",
        "outubro": "Outubro",
        "out": "Outubro",
        "novembro": "Novembro",
        "nov": "Novembro",
        "dezembro": "Dezembro",
        "dez": "Dezembro",
    }

    nome = str(nome_arquivo or "").lower()
    nome = (
        nome.replace("ç", "c")
        .replace("ã", "a")
        .replace("á", "a")
        .replace("â", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ú", "u")
    )
    nome_busca = re.sub(r"[^a-z0-9]+", " ", nome).strip()

    mes_encontrado = ""
    for chave, nome_mes in meses.items():
        if re.search(
            rf"(?<![a-z]){re.escape(chave)}(?![a-z])",
            nome_busca,
        ):
            mes_encontrado = nome_mes
            break

    ano_encontrado = ""
    achado_ano = re.search(r"\b(20\d{2})\b", nome_busca)
    if achado_ano:
        ano_encontrado = achado_ano.group(1)

    if mes_encontrado and ano_encontrado:
        return f"{mes_encontrado}/{ano_encontrado}"

    if mes_encontrado:
        return f"{mes_encontrado}/{datetime.now().year}"

    meses_numero = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }

    agora = datetime.now()
    return f"{meses_numero[agora.month]}/{agora.year}"


def gerar_pdf_imobiliaria_mes_atual(
    nome_imobiliaria,
    periodo,
    nome_arquivo,
    receita,
    inadimplencia,
    vacancia,
    ticket,
    total_imoveis,
    total_ocupados,
    total_vagos,
    contratos_ativos_qtd,
    contratos_vencendo_qtd,
    receita_perdida,
    percentual_inadimplencia_valor,
    eficiencia,
    score,
    classificacao,
    resumo_score,
    diagnostico,
    insights,
    df_imoveis,
    df_contratos,
):
    """
    Relatório mensal simples alinhado ao Painel Cliente aprovado:
    1. Visão geral
    2. Riscos e impactos financeiros
    3. Ranking de prioridades
    4. Plano de ação do mês
    """
    buffer = BytesIO()
    largura, altura = landscape(A4)
    c = pdf_canvas.Canvas(buffer, pagesize=(largura, altura))

    # Paleta
    azul_escuro = colors.HexColor("#0F2742")
    azul = colors.HexColor("#2563EB")
    azul_claro = colors.HexColor("#EAF2FF")
    verde = colors.HexColor("#16A34A")
    vermelho = colors.HexColor("#DC2626")
    vermelho_claro = colors.HexColor("#FEF2F2")
    laranja = colors.HexColor("#EA580C")
    amarelo = colors.HexColor("#D97706")
    amarelo_claro = colors.HexColor("#FFFBEB")
    ciano = colors.HexColor("#0891B2")
    roxo = colors.HexColor("#7C3AED")
    cinza_900 = colors.HexColor("#0F172A")
    cinza_700 = colors.HexColor("#334155")
    cinza_500 = colors.HexColor("#64748B")
    cinza_300 = colors.HexColor("#CBD5E1")
    cinza_200 = colors.HexColor("#E2E8F0")
    cinza_100 = colors.HexColor("#F8FAFC")
    branco = colors.white

    margem = 24
    largura_util = largura - (margem * 2)
    data_emissao = datetime.now().strftime("%d/%m/%Y %H:%M")

    def limpar_texto(valor, padrao="Não informado"):
        texto = str(valor or "")
        texto = re.sub(
            r"[■●◆▪◼◾◻◽⬛⬜🔴🟠🟡🟢🔵🟣⚫⚪]+",
            "",
            texto,
        )
        texto = re.sub(r"\s+", " ", texto).strip()
        return texto or padrao

    def moeda(valor):
        try:
            texto = f"{float(valor):,.2f}"
            texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
            return f"R$ {texto}"
        except Exception:
            return "R$ 0,00"

    def percentual(valor, casas=1):
        try:
            return f"{float(valor):.{casas}f}%".replace(".", ",")
        except Exception:
            return "0,0%"

    def quebrar_linhas(texto, largura_max, fonte="Helvetica", tamanho=8):
        palavras = limpar_texto(texto).split()
        linhas = []
        atual = ""
        for palavra in palavras:
            tentativa = f"{atual} {palavra}".strip()
            if c.stringWidth(tentativa, fonte, tamanho) <= largura_max:
                atual = tentativa
            else:
                if atual:
                    linhas.append(atual)
                atual = palavra
        if atual:
            linhas.append(atual)
        return linhas

    def desenhar_texto(
        texto,
        x,
        y,
        largura_max,
        fonte="Helvetica",
        tamanho=8,
        cor=cinza_700,
        entrelinha=10,
        max_linhas=None,
    ):
        linhas = quebrar_linhas(texto, largura_max, fonte, tamanho)
        if max_linhas:
            linhas = linhas[:max_linhas]
        c.setFont(fonte, tamanho)
        c.setFillColor(cor)
        for linha in linhas:
            c.drawString(x, y, linha)
            y -= entrelinha
        return y

    classificacao_limpa = limpar_texto(classificacao, "Não classificado")
    classificacao_lower = (
        unicodedata.normalize("NFKD", classificacao_limpa.lower())
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    if "crit" in classificacao_lower:
        status_cor = vermelho
    elif "aten" in classificacao_lower:
        status_cor = amarelo
    else:
        status_cor = verde

    def cabecalho(numero_pagina, titulo, subtitulo):
        c.setFillColor(azul_escuro)
        c.roundRect(
            margem,
            altura - 76,
            largura_util,
            50,
            12,
            fill=1,
            stroke=0,
        )
        c.setFillColor(branco)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(margem + 18, altura - 49, titulo)
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#D9F4FF"))
        c.drawString(margem + 18, altura - 64, subtitulo)

        c.setFillColor(status_cor)
        c.roundRect(largura - 164, altura - 69, 120, 36, 8, fill=1, stroke=0)
        c.setFillColor(branco)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(
            largura - 104,
            altura - 47,
            classificacao_limpa.upper(),
        )
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(
            largura - 104,
            altura - 63,
            f"{float(score):.0f}/100",
        )

        c.setStrokeColor(cinza_300)
        c.line(margem, 23, largura - margem, 23)
        c.setFillColor(cinza_500)
        c.setFont("Helvetica", 7)
        c.drawString(margem, 11, "TechDadosBR Inteligência Imobiliária")
        c.drawRightString(
            largura - margem,
            11,
            f"{limpar_texto(nome_imobiliaria)} | "
            f"{limpar_texto(periodo)} | Página {numero_pagina}",
        )

    def rodape(numero_pagina):
        c.setStrokeColor(cinza_300)
        c.line(margem, 23, largura - margem, 23)
        c.setFillColor(cinza_500)
        c.setFont("Helvetica", 7)
        c.drawString(
            margem,
            11,
            "TechDadosBR Inteligência Imobiliária",
        )
        c.drawRightString(
            largura - margem,
            11,
            f"{limpar_texto(nome_imobiliaria)} | "
            f"{limpar_texto(periodo)} | Página {numero_pagina}",
        )

    def card(x, y, w, h, titulo, valor, subtitulo, cor):
        c.setFillColor(branco)
        c.setStrokeColor(cinza_300)
        c.setLineWidth(0.7)
        c.roundRect(x, y, w, h, 9, fill=1, stroke=1)

        c.setFillColor(cor)
        c.roundRect(x, y + h - 5, w, 5, 9, fill=1, stroke=0)

        compacto = h <= 54
        titulo_tamanho = 6.2 if compacto else 7
        titulo_y = y + h - (15 if compacto else 18)

        c.setFillColor(cinza_500)
        c.setFont("Helvetica-Bold", titulo_tamanho)
        c.drawString(x + 10, titulo_y, titulo.upper())

        valor_texto = str(valor)
        tamanho_valor = 13 if compacto else 15
        tamanho_minimo = 9.5 if compacto else 10.5

        while (
            tamanho_valor > tamanho_minimo
            and c.stringWidth(
                valor_texto,
                "Helvetica-Bold",
                tamanho_valor,
            ) > (w - 20)
        ):
            tamanho_valor -= 0.5

        valor_y = y + (17 if compacto else 22)
        c.setFillColor(cinza_900)
        c.setFont("Helvetica-Bold", tamanho_valor)
        c.drawString(x + 10, valor_y, valor_texto)

        subtitulo_tamanho = 5.8 if compacto else 6.8
        subtitulo_y = y + (6 if compacto else 10)
        desenhar_texto(
            subtitulo,
            x + 10,
            subtitulo_y,
            w - 20,
            tamanho=subtitulo_tamanho,
            cor=cinza_500,
            entrelinha=7,
            max_linhas=1,
        )

    def titulo_secao(texto_titulo, y):
        c.setFillColor(cinza_900)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margem, y, texto_titulo)
        return y - 14

    def tabela_pdf(
        dados,
        x,
        y_topo,
        larguras,
        alturas,
        cabecalhos,
        alinhamentos=None,
        destaques=None,
        tamanho=7.2,
    ):
        """
        dados: lista de listas
        destaques: {(linha, coluna): (fundo, cor_texto, fonte)}
        linha 0 nos destaques refere-se à primeira linha de dados.
        """
        total_w = sum(larguras)
        altura_cabecalho = 28
        c.setFillColor(azul_claro)
        c.setStrokeColor(cinza_300)
        c.roundRect(
            x,
            y_topo - altura_cabecalho,
            total_w,
            altura_cabecalho,
            6,
            fill=1,
            stroke=1,
        )

        x_cursor = x
        c.setFillColor(cinza_900)
        c.setFont("Helvetica-Bold", 7.2)
        for idx, cab in enumerate(cabecalhos):
            desenhar_texto(
                cab,
                x_cursor + 6,
                y_topo - 11,
                larguras[idx] - 12,
                fonte="Helvetica-Bold",
                tamanho=7.2,
                cor=cinza_900,
                entrelinha=8,
                max_linhas=2,
            )
            x_cursor += larguras[idx]

        y = y_topo - altura_cabecalho
        for linha_idx, linha in enumerate(dados):
            altura_linha = alturas[linha_idx] if linha_idx < len(alturas) else 30
            y -= altura_linha
            c.setFillColor(branco if linha_idx % 2 == 0 else cinza_100)
            c.rect(x, y, total_w, altura_linha, fill=1, stroke=0)

            x_cursor = x
            for col_idx, valor in enumerate(linha):
                fundo = None
                cor_texto = cinza_700
                fonte = "Helvetica"
                if destaques and (linha_idx, col_idx) in destaques:
                    fundo, cor_texto, fonte = destaques[(linha_idx, col_idx)]
                    if fundo:
                        c.setFillColor(fundo)
                        c.rect(
                            x_cursor,
                            y,
                            larguras[col_idx],
                            altura_linha,
                            fill=1,
                            stroke=0,
                        )

                alinhamento = (
                    alinhamentos[col_idx]
                    if alinhamentos and col_idx < len(alinhamentos)
                    else "left"
                )

                if alinhamento == "center":
                    c.setFillColor(cor_texto)
                    c.setFont(fonte, tamanho)
                    c.drawCentredString(
                        x_cursor + (larguras[col_idx] / 2),
                        y + (altura_linha / 2) - 3,
                        limpar_texto(valor),
                    )
                else:
                    desenhar_texto(
                        valor,
                        x_cursor + 6,
                        y + altura_linha - 11,
                        larguras[col_idx] - 12,
                        fonte=fonte,
                        tamanho=tamanho,
                        cor=cor_texto,
                        entrelinha=tamanho + 2,
                        max_linhas=3,
                    )
                x_cursor += larguras[col_idx]

            c.setStrokeColor(cinza_200)
            c.line(x, y, x + total_w, y)

        # linhas verticais e contorno
        altura_total = altura_cabecalho + sum(
            alturas[:len(dados)]
        )
        x_cursor = x
        c.setStrokeColor(cinza_300)
        for largura_coluna in larguras:
            c.line(
                x_cursor,
                y_topo - altura_total,
                x_cursor,
                y_topo,
            )
            x_cursor += largura_coluna
        c.line(x + total_w, y_topo - altura_total, x + total_w, y_topo)
        c.rect(x, y_topo - altura_total, total_w, altura_total, fill=0, stroke=1)
        return y_topo - altura_total

    # Dados premium
    ranking = montar_ranking_prioridades(
        df_imoveis,
        df_contratos,
        limite=10,
    )
    plano = montar_plano_acao_mensal(
        df_imoveis,
        df_contratos,
        limite=10,
    )
    contratos_prioritarios, resumo_contratos = preparar_contratos_prioritarios(
        df_contratos
    )
    top_vagos = _top_imoveis_vagos_risco(df_imoveis, limite=5)
    riscos_imoveis = calcular_indice_risco_imoveis(df_imoveis)

    contratos_criticos = int(resumo_contratos.get("criticos", 0))
    imoveis_criticos = (
        int((riscos_imoveis["Classificação"] == "CRÍTICO").sum())
        if not riscos_imoveis.empty
        else 0
    )
    valor_contratos_atencao = float(
        resumo_contratos.get("valor_mensal", 0.0)
    )

    if not ranking.empty:
        primeira = ranking.iloc[0]
        prioridade_1 = (
            f"{primeira['Tipo']} {primeira['Identificação']}: "
            f"{primeira['Ação recomendada']}"
        )
    else:
        prioridade_1 = "Revisar os itens críticos identificados no painel."

    # ==================================================
    # PÁGINA 1 - VISÃO GERAL
    # ==================================================
    cabecalho(
        1,
        "Relatório executivo imobiliário",
        "Visão geral e diagnóstico do período analisado",
    )

    c.setFillColor(cinza_500)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(margem, altura - 94, "IMOBILIÁRIA")
    c.drawString(285, altura - 94, "PERÍODO")
    c.drawString(430, altura - 94, "ARQUIVO")
    c.drawString(660, altura - 94, "EMISSÃO")

    c.setFillColor(cinza_900)
    c.setFont("Helvetica", 8)
    c.drawString(margem, altura - 107, limpar_texto(nome_imobiliaria))
    c.drawString(285, altura - 107, limpar_texto(periodo))
    c.drawString(430, altura - 107, limpar_texto(nome_arquivo))
    c.drawString(660, altura - 107, data_emissao)

    c.setStrokeColor(cinza_300)
    c.line(margem, altura - 117, largura - margem, altura - 117)

    y = titulo_secao("Visão geral", altura - 139)

    gap = 8
    card_w = (largura_util - (4 * gap)) / 5
    card_h = 66
    cards_y = y - card_h

    card(margem, cards_y, card_w, card_h, "Score", f"{float(score):.0f}/100", "Saúde geral da carteira", status_cor)
    card(margem + (card_w + gap), cards_y, card_w, card_h, "Classificação", classificacao_limpa, "Nível atual de atenção", status_cor)
    card(margem + (card_w + gap) * 2, cards_y, card_w, card_h, "Receita contratada", moeda(receita), "Base mensal da carteira", verde)
    card(margem + (card_w + gap) * 3, cards_y, card_w, card_h, "Inadimplência", moeda(inadimplencia), f"{percentual(percentual_inadimplencia_valor)} da receita", vermelho)
    card(margem + (card_w + gap) * 4, cards_y, card_w, card_h, "Vacância", percentual(vacancia), f"{int(total_vagos)} de {int(total_imoveis)} imóveis", laranja)

    # Faixa visível do score, logo abaixo dos indicadores.
    legenda_score_y = cards_y - 34
    c.setFillColor(colors.HexColor("#EAF2FF"))
    c.setStrokeColor(colors.HexColor("#2563EB"))
    c.setLineWidth(1)
    c.roundRect(
        margem,
        legenda_score_y,
        largura_util,
        25,
        6,
        fill=1,
        stroke=1,
    )

    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.setFont("Helvetica-Bold", 7.4)
    c.drawString(
        margem + 12,
        legenda_score_y + 9,
        "ESCALA DO SCORE",
    )

    c.setFont("Helvetica", 7.4)
    c.drawString(
        margem + 94,
        legenda_score_y + 9,
        "0 a 49 = Crítico | 50 a 79 = Atenção | 80 a 100 = Saudável",
    )

    diag_y = cards_y - 143
    c.setFillColor(vermelho_claro)
    c.setStrokeColor(colors.HexColor("#FCA5A5"))
    c.roundRect(margem, diag_y, largura_util, 100, 10, fill=1, stroke=1)
    c.setFillColor(vermelho)
    c.roundRect(margem, diag_y, 6, 100, 3, fill=1, stroke=0)

    c.setFillColor(cinza_900)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margem + 16, diag_y + 80, "Diagnóstico executivo")

    col_gap = 10
    col_w = (largura_util - 32 - (3 * col_gap)) / 4
    x0 = margem + 16
    titulos_diag = [
        "SITUAÇÃO DO MÊS",
        "IMPACTO FINANCEIRO",
        "PONTOS CRÍTICOS",
        "PRIMEIRA PRIORIDADE",
    ]
    textos_diag = [
        (
            f"Carteira em nível {classificacao_limpa}, com foco principal "
            f"em {'inadimplência' if float(percentual_inadimplencia_valor) >= float(vacancia) else 'vacância'}."
        ),
        (
            f"{moeda(inadimplencia)} de saldo inadimplente e "
            f"{moeda(abs(float(receita_perdida)))} de perda mensal estimada por vacância."
        ),
        (
            f"{contratos_criticos} contratos críticos e "
            f"{imoveis_criticos} imóveis críticos exigem acompanhamento."
        ),
        prioridade_1,
    ]

    for idx in range(4):
        x_col = x0 + idx * (col_w + col_gap)
        c.setFillColor(cinza_500)
        c.setFont("Helvetica-Bold", 6.6)
        c.drawString(x_col, diag_y + 62, titulos_diag[idx])
        desenhar_texto(
            textos_diag[idx],
            x_col,
            diag_y + 47,
            col_w,
            tamanho=7.5,
            cor=cinza_700,
            entrelinha=9,
            max_linhas=4,
        )

    c.setStrokeColor(colors.HexColor("#FECACA"))
    c.line(margem + 16, diag_y + 24, largura - margem - 16, diag_y + 24)
    c.setFillColor(cinza_900)
    c.setFont("Helvetica-Bold", 7.6)
    c.drawString(margem + 16, diag_y + 11, "Recomendação gerencial:")
    desenhar_texto(
        "Executar primeiro as ações com prazo imediato e acompanhar semanalmente "
        "a redução da inadimplência, da vacância e dos contratos em risco.",
        margem + 112,
        diag_y + 11,
        largura_util - 130,
        tamanho=7.6,
        cor=cinza_700,
        max_linhas=1,
    )

    y_cards2 = diag_y - 84
    card_w2 = (largura_util - (3 * gap)) / 4
    card(margem, y_cards2, card_w2, 64, "Perda mensal por vacância", moeda(abs(float(receita_perdida))), "Receita potencial não realizada", laranja)
    card(margem + card_w2 + gap, y_cards2, card_w2, 64, "Eficiência de ocupação", percentual(eficiencia), f"{int(total_ocupados)} imóveis ocupados", azul)
    card(margem + (card_w2 + gap) * 2, y_cards2, card_w2, 64, "Ticket médio", moeda(ticket), "Valor médio mensal", ciano)
    card(margem + (card_w2 + gap) * 3, y_cards2, card_w2, 64, "Contratos ativos", str(int(contratos_ativos_qtd)), "Contratos monitorados", roxo)

    rodape(1)
    c.showPage()

    # ==================================================
    # PÁGINA 2 - RISCOS FINANCEIROS
    # ==================================================
    cabecalho(
        2,
        "Riscos e impactos financeiros",
        "Valores apresentados separadamente conforme sua natureza",
    )

    y = altura - 104
    c.setFillColor(azul_claro)
    c.setStrokeColor(colors.HexColor("#93C5FD"))
    c.roundRect(margem, y - 58, largura_util, 58, 10, fill=1, stroke=1)
    c.setFillColor(azul)
    c.roundRect(margem, y - 58, 6, 58, 3, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.setFont("Helvetica-Bold", 7)
    c.drawString(margem + 16, y - 17, "PANORAMA EXECUTIVO")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margem + 16, y - 39, "3 frentes financeiras exigem ação")
    c.setFont("Helvetica", 7.5)
    c.drawString(
        margem + 16,
        y - 52,
        "Inadimplência acumulada, perda mensal por vacância e receita mensal sob atenção contratual.",
    )

    riscos_y = y - 135
    risco_w = (largura_util - (2 * gap)) / 3
    card(margem, riscos_y, risco_w, 62, "Inadimplência", moeda(inadimplencia), "Saldo acumulado vencido e ainda não recebido", vermelho)
    card(margem + risco_w + gap, riscos_y, risco_w, 62, "Vacância", moeda(abs(float(receita_perdida))), "Perda estimada por mês com imóveis vagos", laranja)
    card(margem + (risco_w + gap) * 2, riscos_y, risco_w, 62, "Contratos em atenção", moeda(valor_contratos_atencao), "Receita mensal vinculada a contratos em atenção", amarelo)

    tabela_topo = riscos_y - 36
    c.setFillColor(cinza_900)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margem, tabela_topo, "Onde agir primeiro")

    metade = (largura_util - gap) / 2
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(margem, tabela_topo - 22, "Imóveis com maior perda acumulada")
    c.drawString(margem + metade + gap, tabela_topo - 22, "Contratos com maior valor exposto")

    dados_vagos = []
    if not top_vagos.empty:
        for _, linha in top_vagos.iterrows():
            dados_vagos.append([
                linha["Imóvel"],
                linha["Bairro"],
                str(int(linha["Dias vagos"])),
                moeda(linha["Aluguel mensal"]),
                moeda(linha["Perda acumulada estimada"]),
            ])

    dados_contratos = []
    if not contratos_prioritarios.empty:
        top_contratos = contratos_prioritarios.sort_values(
            "_valor_num",
            ascending=False,
        ).head(5)
        for _, linha in top_contratos.iterrows():
            dados_contratos.append([
                linha["Prioridade"],
                linha["Contrato"],
                linha["Imóvel"],
                linha["Cliente"],
                linha["Prazo"],
                linha["Valor mensal"],
            ])

    y_tabela = tabela_topo - 32
    tabela_pdf(
        dados_vagos,
        margem,
        y_tabela,
        [48, 95, 58, 85, metade - 286],
        [31] * len(dados_vagos),
        ["Imóvel", "Bairro", "Dias vagos", "Aluguel mensal", "Perda acumulada"],
        tamanho=6.8,
    )
    tabela_pdf(
        dados_contratos,
        margem + metade + gap,
        y_tabela,
        [52, 58, 48, 70, 88, metade - 316],
        [31] * len(dados_contratos),
        ["Prioridade", "Contrato", "Imóvel", "Cliente", "Prazo", "Valor mensal"],
        tamanho=6.6,
    )

    if not top_vagos.empty:
        principal_vago = top_vagos.iloc[0]
        alerta = (
            f"Prioridade sugerida: atuar primeiro no imóvel "
            f"{principal_vago['Imóvel']} ({principal_vago['Bairro']}), "
            f"com {int(principal_vago['Dias vagos'])} dias vagos e perda "
            f"acumulada estimada de {moeda(principal_vago['Perda acumulada estimada'])}."
        )
    else:
        alerta = "Prioridade sugerida: tratar primeiro o item de maior risco identificado no painel."

    c.setFillColor(amarelo_claro)
    c.setStrokeColor(colors.HexColor("#FDE68A"))
    c.roundRect(margem, 42, largura_util, 30, 7, fill=1, stroke=1)
    desenhar_texto(
        alerta,
        margem + 10,
        54,
        largura_util - 20,
        tamanho=7.5,
        cor=cinza_700,
        max_linhas=1,
    )

    rodape(2)
    c.showPage()

    # ==================================================
    # PÁGINA 3 - RANKING DE PRIORIDADES
    # ==================================================
    cabecalho(
        3,
        "Ranking de prioridades",
        "Ordem de atuação por risco, prazo e impacto financeiro",
    )

    y = altura - 102

    criticas = (
        int(ranking["Nível"].isin(["CRÍTICO", "CRÍTICA"]).sum())
        if not ranking.empty
        else 0
    )
    qtd_imoveis = (
        int((ranking["Tipo"] == "Imóvel").sum())
        if not ranking.empty
        else 0
    )
    qtd_contratos = (
        int((ranking["Tipo"] == "Contrato").sum())
        if not ranking.empty
        else 0
    )
    impacto_ranking = (
        float(ranking["Impacto mensal"].sum())
        if not ranking.empty
        else 0.0
    )

    resumo_y = y - 64
    resumo_w = (largura_util - (2 * gap)) / 3
    card(
        margem,
        resumo_y,
        resumo_w,
        50,
        "Prioridades analisadas",
        str(len(ranking)),
        "Itens ordenados por urgência e impacto",
        vermelho,
    )
    card(
        margem + resumo_w + gap,
        resumo_y,
        resumo_w,
        50,
        "Composição do ranking",
        f"{qtd_contratos} contratos + {qtd_imoveis} imóveis",
        "Todos reunidos em uma única ordem de atuação",
        azul,
    )
    card(
        margem + (resumo_w + gap) * 2,
        resumo_y,
        resumo_w,
        50,
        "Impacto mensal monitorado",
        moeda(impacto_ranking),
        "Soma dos impactos dos itens priorizados",
        roxo,
    )

    dados_ranking = []
    destaques_ranking = {}
    if not ranking.empty:
        for linha_idx, (_, linha) in enumerate(ranking.head(10).iterrows()):
            nivel_padronizado = (
                "CRÍTICO"
                if str(linha["Nível"]).upper() in {"CRÍTICO", "CRÍTICA"}
                else str(linha["Nível"]).upper()
            )

            dados_ranking.append([
                str(int(linha["Prioridade"])),
                linha["Tipo"],
                linha["Identificação"],
                linha["Local/Cliente"],
                nivel_padronizado,
                str(int(linha["Índice"])),
                moeda(linha["Impacto mensal"]),
                linha["Motivo"],
                linha["Ação recomendada"],
            ])
            if linha_idx == 0:
                destaques_ranking[(linha_idx, 0)] = (
                    vermelho,
                    branco,
                    "Helvetica-Bold",
                )
            else:
                destaques_ranking[(linha_idx, 0)] = (
                    None,
                    cinza_900,
                    "Helvetica-Bold",
                )
            destaques_ranking[(linha_idx, 4)] = (
                colors.HexColor("#FEE2E2"),
                colors.HexColor("#991B1B"),
                "Helvetica-Bold",
            )

    legenda_y = resumo_y - 28
    c.setFillColor(azul_claro)
    c.setStrokeColor(colors.HexColor("#BFDBFE"))
    c.roundRect(
        margem,
        legenda_y,
        largura_util,
        20,
        5,
        fill=1,
        stroke=1,
    )
    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.setFont("Helvetica-Bold", 7)
    c.drawString(
        margem + 10,
        legenda_y + 7,
        "Leitura do ranking: contratos e imóveis aparecem juntos; a prioridade 1 deve ser tratada primeiro.",
    )

    y_ranking = legenda_y - 8
    tabela_pdf(
        dados_ranking,
        margem,
        y_ranking,
        [40, 48, 60, 98, 56, 40, 72, 102, largura_util - 516],
        [28] * len(dados_ranking),
        ["#", "Tipo", "Identificação", "Cliente / Local", "Nível de risco", "Índice", "Impacto", "Motivo", "Ação recomendada"],
        alinhamentos=["center", "left", "left", "left", "left", "center", "left", "left", "left"],
        destaques=destaques_ranking,
        tamanho=6.1,
    )

    if not ranking.empty:
        primeira = ranking.iloc[0]
        alerta_ranking = (
            f"Ação nº 1: {primeira['Tipo']} {primeira['Identificação']} | "
            f"{primeira['Motivo']} | impacto mensal de "
            f"{moeda(primeira['Impacto mensal'])} | "
            f"{primeira['Ação recomendada']}"
        )
        c.setFillColor(amarelo_claro)
        c.setStrokeColor(colors.HexColor("#FDE68A"))
        c.roundRect(margem, 42, largura_util, 30, 7, fill=1, stroke=1)
        desenhar_texto(
            alerta_ranking,
            margem + 10,
            54,
            largura_util - 20,
            tamanho=7.3,
            cor=cinza_700,
            max_linhas=1,
        )

    rodape(3)
    c.showPage()

    # ==================================================
    # PÁGINA 4 - PLANO DE AÇÃO
    # ==================================================
    cabecalho(
        4,
        "Plano de ação do mês",
        "Responsáveis sugeridos, prazos e impacto relacionado",
    )

    y = altura - 102

    acoes_prioritarias = len(plano) if not plano.empty else 0
    acoes_urgentes = (
        int(
            plano["Prazo recomendado"].isin(
                ["Hoje", "Até 2 dias", "Até 3 dias"]
            ).sum()
        )
        if not plano.empty
        else 0
    )
    qtd_contratos_plano = (
        int((plano["Tipo"] == "Contrato").sum())
        if not plano.empty
        else 0
    )
    qtd_imoveis_plano = (
        int((plano["Tipo"] == "Imóvel").sum())
        if not plano.empty
        else 0
    )
    impacto_plano = (
        float(plano["Impacto mensal"].sum())
        if not plano.empty
        else 0.0
    )

    resumo_y = y - 64
    resumo_w = (largura_util - (3 * gap)) / 4
    card(margem, resumo_y, resumo_w, 50, "Ações prioritárias", str(acoes_prioritarias), "Tarefas do mês", vermelho)
    card(margem + resumo_w + gap, resumo_y, resumo_w, 50, "Ações urgentes", str(acoes_urgentes), "Execução imediata", laranja)
    card(margem + (resumo_w + gap) * 2, resumo_y, resumo_w, 50, "Contratos / Imóveis", f"{qtd_contratos_plano} / {qtd_imoveis_plano}", "Distribuição das ações", azul)
    card(margem + (resumo_w + gap) * 3, resumo_y, resumo_w, 50, "Impacto mensal relacionado", moeda(impacto_plano), "Valor relacionado às ações", roxo)

    dados_plano = []
    destaques_plano = {}
    if not plano.empty:
        for linha_idx, (_, linha) in enumerate(plano.head(10).iterrows()):
            dados_plano.append([
                str(int(linha["Prioridade"])),
                linha["Tipo"],
                linha["Identificação"],
                linha["Local/Cliente"],
                linha["Ação"],
                linha["Responsável sugerido"],
                linha["Prazo recomendado"],
                moeda(linha["Impacto mensal"]),
                linha["Status"],
            ])
            if linha["Prazo recomendado"] == "Hoje":
                destaques_plano[(linha_idx, 6)] = (
                    colors.HexColor("#FEE2E2"),
                    colors.HexColor("#991B1B"),
                    "Helvetica-Bold",
                )
            else:
                destaques_plano[(linha_idx, 6)] = (
                    colors.HexColor("#FEF3C7"),
                    colors.HexColor("#92400E"),
                    "Helvetica-Bold",
                )

    y_plano = resumo_y - 12
    tabela_pdf(
        dados_plano,
        margem,
        y_plano,
        [36, 44, 58, 90, 220, 96, 66, 74, largura_util - 684],
        [28] * len(dados_plano),
        ["#", "Tipo", "Identificação", "Cliente / Local", "Ação", "Responsável", "Prazo", "Impacto", "Status"],
        alinhamentos=["center", "left", "left", "left", "left", "left", "center", "left", "left"],
        destaques=destaques_plano,
        tamanho=6.2,
    )

    if not plano.empty:
        primeira_acao = plano.iloc[0]
        alerta_plano = (
            f"Começar por: {primeira_acao['Tipo']} "
            f"{primeira_acao['Identificação']} | "
            f"{primeira_acao['Ação']} | responsável sugerido: "
            f"{primeira_acao['Responsável sugerido']} | "
            f"prazo: {primeira_acao['Prazo recomendado']}."
        )
        c.setFillColor(amarelo_claro)
        c.setStrokeColor(colors.HexColor("#FDE68A"))
        c.roundRect(margem, 42, largura_util, 30, 7, fill=1, stroke=1)
        desenhar_texto(
            alerta_plano,
            margem + 10,
            54,
            largura_util - 20,
            tamanho=7.3,
            cor=cinza_700,
            max_linhas=1,
        )

    rodape(4)
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes



# ==================================================
# RELATÓRIO PDF COMPARATIVO
# ==================================================

def gerar_pdf_comparativo_imobiliaria(
    nome_imobiliaria,
    periodo_atual,
    periodo_anterior,
    nome_arquivo_atual,
    nome_arquivo_anterior,
    receita_atual,
    receita_anterior,
    inadimplencia_atual,
    inadimplencia_anterior,
    vacancia_atual,
    vacancia_anterior,
    score_atual,
    score_anterior,
    ocupados_atual,
    ocupados_anterior,
    vagos_atual,
    vagos_anterior,
    contratos_ativos_atual,
    contratos_ativos_anterior,
    ticket_atual,
    ticket_anterior,
):
    buffer = BytesIO()
    largura, altura = landscape(A4)
    c = pdf_canvas.Canvas(buffer, pagesize=(largura, altura))

    azul_escuro = colors.HexColor("#0F2742")
    azul = colors.HexColor("#2563EB")
    azul_claro = colors.HexColor("#EAF2FF")
    verde = colors.HexColor("#16A34A")
    vermelho = colors.HexColor("#DC2626")
    laranja = colors.HexColor("#EA580C")
    cinza_900 = colors.HexColor("#0F172A")
    cinza_700 = colors.HexColor("#334155")
    cinza_500 = colors.HexColor("#64748B")
    cinza_300 = colors.HexColor("#CBD5E1")
    cinza_100 = colors.HexColor("#F8FAFC")
    branco = colors.white

    margem = 24
    largura_util = largura - (2 * margem)

    def moeda(valor):
        try:
            texto = f"{float(valor):,.2f}"
            texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
            return f"R$ {texto}"
        except Exception:
            return "R$ 0,00"

    def percentual(valor):
        try:
            return f"{float(valor):.1f}%".replace(".", ",")
        except Exception:
            return "0,0%"

    def delta_percentual(atual, anterior):
        try:
            if float(anterior) == 0:
                return None
            return ((float(atual) - float(anterior)) / abs(float(anterior))) * 100
        except Exception:
            return None

    def delta_texto(atual, anterior, tipo):
        if tipo == "percentual_pp":
            delta = float(atual) - float(anterior)
            numero_formatado = f"{delta:+.1f}".replace(".", ",")
            return f"{numero_formatado} p.p.", delta
        if tipo == "pontos":
            delta = int(round(float(atual) - float(anterior)))
            return f"{delta:+d} pontos", float(delta)
        if tipo == "inteiro":
            delta = int(round(float(atual) - float(anterior)))
            return f"{delta:+d}", float(delta)

        delta = delta_percentual(atual, anterior)
        if delta is None:
            return "—", None
        return f"{delta:+.1f}%".replace(".", ","), delta

    def cor_status(delta, positivo_eh_bom=True):
        if delta is None or abs(float(delta)) < 0.05:
            return cinza_500, "ESTÁVEL"
        melhorou = delta > 0 if positivo_eh_bom else delta < 0
        return (verde, "MELHORA") if melhorou else (vermelho, "ATENÇÃO")

    def cabecalho(pagina, titulo, subtitulo):
        c.setFillColor(azul_escuro)
        c.roundRect(margem, altura - 76, largura_util, 50, 12, fill=1, stroke=0)
        c.setFillColor(branco)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(margem + 18, altura - 49, titulo)
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#D9F4FF"))
        c.drawString(margem + 18, altura - 64, subtitulo)

        c.setStrokeColor(cinza_300)
        c.line(margem, 23, largura - margem, 23)
        c.setFillColor(cinza_500)
        c.setFont("Helvetica", 7)
        c.drawString(margem, 11, "TechDadosBR Inteligência Imobiliária")
        c.drawRightString(
            largura - margem,
            11,
            f"{nome_imobiliaria} | {periodo_anterior} x {periodo_atual} | Página {pagina}",
        )

    def card_comparativo(
        x, y, w, h, titulo,
        anterior_fmt, atual_fmt,
        variacao_texto, delta_num,
        positivo_eh_bom=True,
    ):
        cor, status = cor_status(delta_num, positivo_eh_bom)

        c.setFillColor(branco)
        c.setStrokeColor(cinza_300)
        c.setLineWidth(0.8)
        c.roundRect(x, y, w, h, 10, fill=1, stroke=1)

        c.setFillColor(cor)
        c.roundRect(x, y + h - 6, w, 6, 10, fill=1, stroke=0)

        c.setFillColor(cinza_500)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 12, y + h - 20, titulo.upper())

        c.setFillColor(cinza_500)
        c.setFont("Helvetica", 6.5)
        c.drawString(x + 12, y + h - 37, "MÊS ANTERIOR")
        c.setFillColor(cinza_900)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x + 12, y + h - 52, anterior_fmt)

        c.setFillColor(cinza_500)
        c.setFont("Helvetica", 6.5)
        c.drawString(x + (w / 2) + 4, y + h - 37, "MÊS ATUAL")
        c.setFillColor(cinza_900)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x + (w / 2) + 4, y + h - 52, atual_fmt)

        c.setStrokeColor(cinza_300)
        c.line(x + 12, y + 23, x + w - 12, y + 23)

        c.setFillColor(cor)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x + 12, y + 9, f"{status}: {variacao_texto}")

    receita_delta_txt, receita_delta = delta_texto(
        receita_atual, receita_anterior, "percentual"
    )
    inad_delta_txt, inad_delta = delta_texto(
        inadimplencia_atual, inadimplencia_anterior, "percentual"
    )
    vac_delta_txt, vac_delta = delta_texto(
        vacancia_atual, vacancia_anterior, "percentual_pp"
    )
    score_delta_txt, score_delta = delta_texto(
        score_atual, score_anterior, "pontos"
    )
    ocup_delta_txt, ocup_delta = delta_texto(
        ocupados_atual, ocupados_anterior, "inteiro"
    )
    vagos_delta_txt, vagos_delta = delta_texto(
        vagos_atual, vagos_anterior, "inteiro"
    )
    ctr_delta_txt, ctr_delta = delta_texto(
        contratos_ativos_atual, contratos_ativos_anterior, "inteiro"
    )
    ticket_delta_txt, ticket_delta = delta_texto(
        ticket_atual, ticket_anterior, "percentual"
    )

    cabecalho(
        1,
        "Relatório comparativo imobiliário",
        "Evolução financeira, operacional e de risco entre os períodos",
    )

    c.setFillColor(cinza_500)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(margem, altura - 96, "IMOBILIÁRIA")
    c.drawString(280, altura - 96, "PERÍODO ANTERIOR")
    c.drawString(450, altura - 96, "PERÍODO ATUAL")
    c.drawString(620, altura - 96, "EMISSÃO")

    c.setFillColor(cinza_900)
    c.setFont("Helvetica", 8)
    c.drawString(margem, altura - 109, str(nome_imobiliaria))
    c.drawString(280, altura - 109, str(periodo_anterior))
    c.drawString(450, altura - 109, str(periodo_atual))
    c.drawString(620, altura - 109, datetime.now().strftime("%d/%m/%Y %H:%M"))

    c.setStrokeColor(cinza_300)
    c.line(margem, altura - 119, largura - margem, altura - 119)

    c.setFillColor(azul_claro)
    c.setStrokeColor(colors.HexColor("#93C5FD"))
    c.roundRect(margem, altura - 178, largura_util, 44, 9, fill=1, stroke=1)

    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margem + 14, altura - 151, "Arquivos comparados")
    c.setFont("Helvetica", 7.5)
    c.drawString(
        margem + 14,
        altura - 166,
        f"Anterior: {nome_arquivo_anterior} | Atual: {nome_arquivo_atual}",
    )

    gap = 10
    card_w = (largura_util - (3 * gap)) / 4
    card_h = 112
    y1 = altura - 307
    y2 = altura - 429

    card_comparativo(margem, y1, card_w, card_h, "Receita",
                     moeda(receita_anterior), moeda(receita_atual),
                     receita_delta_txt, receita_delta, True)
    card_comparativo(margem + card_w + gap, y1, card_w, card_h, "Inadimplência",
                     moeda(inadimplencia_anterior), moeda(inadimplencia_atual),
                     inad_delta_txt, inad_delta, False)
    card_comparativo(margem + (card_w + gap) * 2, y1, card_w, card_h, "Vacância",
                     percentual(vacancia_anterior), percentual(vacancia_atual),
                     vac_delta_txt, vac_delta, False)
    card_comparativo(margem + (card_w + gap) * 3, y1, card_w, card_h, "Score",
                     f"{int(round(score_anterior))}/100",
                     f"{int(round(score_atual))}/100",
                     score_delta_txt, score_delta, True)

    card_comparativo(margem, y2, card_w, card_h, "Imóveis ocupados",
                     str(int(ocupados_anterior)), str(int(ocupados_atual)),
                     ocup_delta_txt, ocup_delta, True)
    card_comparativo(margem + card_w + gap, y2, card_w, card_h, "Imóveis vagos",
                     str(int(vagos_anterior)), str(int(vagos_atual)),
                     vagos_delta_txt, vagos_delta, False)
    card_comparativo(margem + (card_w + gap) * 2, y2, card_w, card_h, "Contratos ativos",
                     str(int(contratos_ativos_anterior)),
                     str(int(contratos_ativos_atual)),
                     ctr_delta_txt, ctr_delta, True)
    card_comparativo(margem + (card_w + gap) * 3, y2, card_w, card_h, "Ticket médio",
                     moeda(ticket_anterior), moeda(ticket_atual),
                     ticket_delta_txt, ticket_delta, True)

    pontos_positivos = []
    pontos_atencao = []
    comparacoes = [
        ("Receita", receita_delta, True),
        ("Inadimplência", inad_delta, False),
        ("Vacância", vac_delta, False),
        ("Score", score_delta, True),
        ("Imóveis ocupados", ocup_delta, True),
        ("Imóveis vagos", vagos_delta, False),
        ("Contratos ativos", ctr_delta, True),
        ("Ticket médio", ticket_delta, True),
    ]
    for titulo, delta, positivo_eh_bom in comparacoes:
        if delta is None or abs(float(delta)) < 0.05:
            continue
        melhorou = delta > 0 if positivo_eh_bom else delta < 0
        (pontos_positivos if melhorou else pontos_atencao).append(titulo)

    c.setFillColor(cinza_100)
    c.setStrokeColor(cinza_300)
    c.roundRect(margem, 45, largura_util, 70, 10, fill=1, stroke=1)
    c.setFillColor(cinza_900)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margem + 12, 96, "Resumo executivo do período")
    c.setFont("Helvetica", 7.5)
    c.setFillColor(cinza_700)
    c.drawString(
        margem + 12,
        79,
        "Melhoras: " + (
            ", ".join(pontos_positivos)
            if pontos_positivos
            else "nenhuma melhora relevante"
        ),
    )
    c.drawString(
        margem + 12,
        63,
        "Pontos de atenção: " + (
            ", ".join(pontos_atencao)
            if pontos_atencao
            else "nenhum alerta relevante"
        ),
    )

    c.showPage()

    cabecalho(
        2,
        "Leitura gerencial do comparativo",
        "Principais movimentos do período e direcionamentos recomendados",
    )

    c.setFillColor(cinza_900)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margem, altura - 105, "Síntese do período")

    blocos = [
        (
            "Financeiro",
            (
                f"A receita passou de {moeda(receita_anterior)} para "
                f"{moeda(receita_atual)}. A inadimplência passou de "
                f"{moeda(inadimplencia_anterior)} para "
                f"{moeda(inadimplencia_atual)}."
            ),
            azul,
        ),
        (
            "Operacional",
            (
                f"A vacância passou de {percentual(vacancia_anterior)} para "
                f"{percentual(vacancia_atual)}. A carteira encerrou o período "
                f"com {int(ocupados_atual)} imóveis ocupados e "
                f"{int(vagos_atual)} imóveis vagos."
            ),
            laranja,
        ),
        (
            "Risco e contratos",
            (
                f"O score passou de {int(round(score_anterior))}/100 para "
                f"{int(round(score_atual))}/100. Os contratos ativos passaram "
                f"de {int(contratos_ativos_anterior)} para "
                f"{int(contratos_ativos_atual)}."
            ),
            vermelho,
        ),
    ]

    y = altura - 135
    for titulo, texto_bloco, cor in blocos:
        c.setFillColor(branco)
        c.setStrokeColor(cinza_300)
        c.roundRect(margem, y - 78, largura_util, 68, 10, fill=1, stroke=1)
        c.setFillColor(cor)
        c.roundRect(margem, y - 78, 6, 68, 3, fill=1, stroke=0)
        c.setFillColor(cinza_900)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margem + 18, y - 28, titulo)
        c.setFillColor(cinza_700)
        c.setFont("Helvetica", 8)
        c.drawString(margem + 18, y - 48, texto_bloco)
        y -= 88

    recomendacoes = []
    if receita_delta is not None and receita_delta < 0:
        recomendacoes.append(
            "Revisar as causas da queda de receita e os contratos com maior impacto."
        )
    if inad_delta is not None and inad_delta > 0:
        recomendacoes.append(
            "Reforçar cobrança e priorizar os maiores saldos inadimplentes."
        )
    if vac_delta is not None and vac_delta > 0:
        recomendacoes.append(
            "Atuar nos imóveis vagos com maior perda potencial."
        )
    if score_delta is not None and score_delta < 0:
        recomendacoes.append(
            "Revisar os fatores que reduziram o score da carteira."
        )
    if not recomendacoes:
        recomendacoes.append(
            "Manter o acompanhamento mensal e preservar os indicadores que melhoraram."
        )

    c.setFillColor(azul_claro)
    c.setStrokeColor(colors.HexColor("#93C5FD"))
    c.roundRect(margem, 88, largura_util, 105, 10, fill=1, stroke=1)
    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margem + 16, 171, "Direcionamento gerencial")
    c.setFillColor(cinza_700)
    c.setFont("Helvetica", 8)
    yy = 151
    for indice, recomendacao in enumerate(recomendacoes[:4], start=1):
        c.drawString(margem + 18, yy, f"{indice}. {recomendacao}")
        yy -= 16

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# ==================================================
# CONFIG
# ==================================================

st.set_page_config(
    page_title="TechDadosBR Imobiliária — Cliente V45",
    page_icon="🏠",
    layout="wide"
)

# ==================================================
# TEMA PADRÃO
# ==================================================

tema_visual = st.session_state.get("tema_visual_imobiliaria", st.session_state.get("tema_visual_imob", "Claro"))

if tema_visual == "Escuro":
    bg = "#0F172A"
    sidebar_bg = "#17223A"
    card = "#111827"
    text = "#F8FAFC"
    muted = "#CBD5E1"
    border = "#334155"
    hero1 = "#132B57"
    hero2 = "#0F3A4A"
else:
    bg = "#F3F6FA"
    sidebar_bg = "#F3F6FA"
    card = "#FFFFFF"
    text = "#0F172A"
    muted = "#475569"
    border = "#CBD5E1"
    hero1 = "#DBEAFE"
    hero2 = "#CFFAFE"

st.markdown(
    f"""
    <style>
        .stApp {{
            background: {bg};
            color: {text};
        }}

        /* Remove a faixa branca superior do Streamlit */
        header[data-testid="stHeader"],
        [data-testid="stHeader"],
        .stAppHeader {{
            background: {bg} !important;
            background-color: {bg} !important;
            box-shadow: none !important;
            border: none !important;
        }}

        [data-testid="stDecoration"] {{
            display: none !important;
        }}

        [data-testid="stToolbar"] {{
            background: transparent !important;
        }}

        [data-testid="stAppViewContainer"] > .main {{
            background: {bg} !important;
            background-color: {bg} !important;
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background: {sidebar_bg} !important;
            border-right: 1px solid {border};
        }}

        section[data-testid="stSidebar"] * {{
            color: {text} !important;
        }}

        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div {{
            color: {text} !important;
        }}

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {{
            color: {text} !important;
        }}

        section[data-testid="stSidebar"] small {{
            color: {muted} !important;
        }}

        /* Selectbox da sidebar */
        section[data-testid="stSidebar"] [data-baseweb="select"] > div {{
            background-color: #FFFFFF !important;
            border-color: {border} !important;
            border-radius: 9px !important;
        }}

        section[data-testid="stSidebar"] [data-baseweb="select"] span {{
            color: #111827 !important;
        }}

        /* Menu lateral: esconder bolinhas apenas do primeiro radio */
        section[data-testid="stSidebar"] div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label > div:first-child {{
            display: none !important;
        }}

        section[data-testid="stSidebar"] div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label {{
            padding-left: 0 !important;
            margin-bottom: 7px !important;
        }}

        /* Aparência: manter bolinhas visíveis */
        section[data-testid="stSidebar"] div[data-testid="stRadio"]:not(:first-of-type) div[role="radiogroup"] label > div:first-child {{
            display: flex !important;
        }}

        /* Seletor Claro/Escuro com bolinhas visíveis */
        .st-key-tema_visual_imobiliaria_v39 div[role="radiogroup"] label > div:first-child {{
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            min-width: 16px !important;
            margin-right: 7px !important;
        }}

        .td-hero-app {{
            background: linear-gradient(135deg, {hero1}, {hero2});
            border: 1px solid {border};
            border-radius: 18px;
            padding: 22px 24px;
            box-shadow: 0 12px 28px rgba(15,23,42,.12);
            margin-bottom: 24px;
        }}

        .td-hero-app-title {{
            color: {text};
            font-size: 31px;
            font-weight: 850;
            margin-bottom: 6px;
        }}

        .td-hero-app-subtitle {{
            color: {muted};
            font-size: 14px;
            line-height: 1.45;
        }}

        /* Sidebar final - força fundo e textos */
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] > div,
        [data-testid="stSidebarContent"],
        [data-testid="stSidebarUserContent"] {{
            background: {sidebar_bg} !important;
            background-color: {sidebar_bg} !important;
        }}

        [data-testid="stSidebar"] * {{
            color: {text} !important;
        }}

        [data-testid="stSidebar"] [data-baseweb="select"],
        [data-testid="stSidebar"] [data-baseweb="select"] * {{
            color: #111827 !important;
        }}

        [data-testid="stSidebar"] [data-baseweb="select"] > div {{
            background: #FFFFFF !important;
            background-color: #FFFFFF !important;
            border: 1px solid {border} !important;
            border-radius: 9px !important;
        }}

        /* Esconder bolinhas somente do primeiro radio/menu */
        [data-testid="stSidebar"] div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label > div:first-child {{
            display: none !important;
        }}

        [data-testid="stSidebar"] div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label {{
            padding-left: 0 !important;
            margin-bottom: 7px !important;
        }}

    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="td-hero-app">
        <div class="td-hero-app-title">🏠 TechDadosBR Inteligência Imobiliária</div>
        <div class="td-hero-app-subtitle">
            Painel exclusivo do cliente para consulta dos indicadores, comparativos e relatórios.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ==================================================
# MENU
# ==================================================

pagina = st.sidebar.radio(
    "Menu",
    [
        "📊 Executivo",
        "🏢 Gestão Carteira",
        "📈 Comparativo",
        "📄 Relatório"
    ]
)

# ==========================================
# APARÊNCIA
# ==========================================

st.sidebar.markdown("### Aparência")

tema_visual = st.sidebar.radio(
    "Tema visual",
    ["Claro", "Escuro"],
    index=0 if st.session_state.get("tema_visual_imobiliaria", st.session_state.get("tema_visual_imob", "Claro")) == "Claro" else 1,
    key="tema_visual_imobiliaria_v39",
    help="Escolha o tema para adaptar a visualização da tela."
)

st.session_state["tema_visual_imob"] = tema_visual
st.session_state["tema_visual_imobiliaria"] = tema_visual

# CSS aplicado depois da escolha do tema para corrigir a sidebar
if tema_visual == "Escuro":
    sidebar_bg_final = "#17223A"
    sidebar_text_final = "#F8FAFC"
    sidebar_muted_final = "#CBD5E1"
    sidebar_border_final = "#334155"
else:
    sidebar_bg_final = "#F3F6FA"
    sidebar_text_final = "#0F172A"
    sidebar_muted_final = "#475569"
    sidebar_border_final = "#CBD5E1"

st.markdown(
    f"""
    <style>
        /* Menu lateral fixo no Streamlit Cloud */
        section[data-testid="stSidebar"],
        [data-testid="stSidebar"] {{
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            transform: translateX(0) !important;
            left: 0 !important;
            min-width: 220px !important;
            width: 220px !important;
            z-index: 9999 !important;
        }}

        section[data-testid="stSidebar"] > div:first-child,
        [data-testid="stSidebar"] > div:first-child {{
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            transform: translateX(0) !important;
            min-width: 220px !important;
            width: 220px !important;
        }}

        /* Impede que o menu seja recolhido no ambiente publicado */
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"] {{
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }}

        /* Sidebar - fundo atualizado depois da escolha do tema */
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div,
        section[data-testid="stSidebar"] div[data-testid="stSidebarContent"],
        section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] {{
            background: {sidebar_bg_final} !important;
            background-color: {sidebar_bg_final} !important;
        }}

        /* Textos da sidebar */
        section[data-testid="stSidebar"] *,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {{
            color: {sidebar_text_final} !important;
        }}

        section[data-testid="stSidebar"] small {{
            color: {sidebar_muted_final} !important;
        }}

        /* Selectbox dos filtros */
        section[data-testid="stSidebar"] [data-baseweb="select"] > div {{
            background-color: #FFFFFF !important;
            border: 1px solid {sidebar_border_final} !important;
            border-radius: 9px !important;
        }}

        section[data-testid="stSidebar"] [data-baseweb="select"] span,
        section[data-testid="stSidebar"] [data-baseweb="select"] div {{
            color: #111827 !important;
        }}

        /* Esconder bolinhas somente do menu principal */
        section[data-testid="stSidebar"] div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label > div:first-child {{
            display: none !important;
        }}

        section[data-testid="stSidebar"] div[data-testid="stRadio"]:first-of-type div[role="radiogroup"] label {{
            padding-left: 0 !important;
            margin-bottom: 7px !important;
        }}

        /* Aparência mantém bolinhas */
        section[data-testid="stSidebar"] div[data-testid="stRadio"]:not(:first-of-type) div[role="radiogroup"] label > div:first-child {{
            display: flex !important;
        }}

        /* Menu lateral em uma única linha */
        section[data-testid="stSidebar"] {{
            min-width: 220px !important;
            width: 220px !important;
        }}

        section[data-testid="stSidebar"] > div:first-child {{
            min-width: 220px !important;
            width: 220px !important;
        }}

        section[data-testid="stSidebar"] div[role="radiogroup"] label {{
            white-space: nowrap !important;
        }}

        section[data-testid="stSidebar"] div[role="radiogroup"] label p,
        section[data-testid="stSidebar"] div[role="radiogroup"] label span {{
            white-space: nowrap !important;
        }}

        /* Seletor Claro/Escuro com bolinhas sempre visíveis */
        .st-key-tema_visual_imobiliaria_v39 div[role="radiogroup"] label > div:first-child {{
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: auto !important;
            min-width: 16px !important;
            margin-right: 7px !important;
        }}

        .st-key-tema_visual_imobiliaria_v39 div[role="radiogroup"] label {{
            display: flex !important;
            align-items: center !important;
            padding-left: 0 !important;
            margin-bottom: 5px !important;
        }}

        /* Abas visíveis nos dois temas */
        [data-testid="stTabs"] [role="tab"],
        [data-baseweb="tab-list"] [role="tab"] {{
            color: {sidebar_muted_final} !important;
            -webkit-text-fill-color: {sidebar_muted_final} !important;
            opacity: 1 !important;
            font-weight: 750 !important;
        }}

        [data-testid="stTabs"] [role="tab"] *,
        [data-baseweb="tab-list"] [role="tab"] * {{
            color: {sidebar_muted_final} !important;
            -webkit-text-fill-color: {sidebar_muted_final} !important;
            opacity: 1 !important;
        }}

        [data-testid="stTabs"] [role="tab"][aria-selected="true"],
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] *,
        [data-baseweb="tab-list"] [role="tab"][aria-selected="true"],
        [data-baseweb="tab-list"] [role="tab"][aria-selected="true"] * {{
            color: #FF4B4B !important;
            -webkit-text-fill-color: #FF4B4B !important;
            opacity: 1 !important;
        }}

        /* Botões legíveis no tema escuro */
        .stButton > button,
        .stDownloadButton > button {{
            background: #2563EB !important;
            color: #FFFFFF !important;
            border: 1px solid #3B82F6 !important;
        }}

        .stButton > button *,
        .stDownloadButton > button * {{
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
        }}

        .stButton > button:disabled,
        .stDownloadButton > button:disabled {{
            background: {"#334155" if tema_visual == "Escuro" else "#CBD5E1"} !important;
            color: {"#CBD5E1" if tema_visual == "Escuro" else "#475569"} !important;
            opacity: 1 !important;
        }}

        /* Upload estável nos dois temas */
        [data-testid="stFileUploader"] section {{
            background: transparent !important;
            border: 1px solid {sidebar_border_final} !important;
            border-radius: 12px !important;
        }}

        [data-testid="stFileUploaderFile"] {{
            background: {"#17223A" if tema_visual == "Escuro" else "#FFFFFF"} !important;
            border: 1px solid {sidebar_border_final} !important;
            border-radius: 10px !important;
        }}

        [data-testid="stFileUploaderFile"] > div {{
            background: transparent !important;
        }}

        [data-testid="stFileUploaderFile"] p,
        [data-testid="stFileUploaderFile"] span,
        [data-testid="stFileUploaderFile"] small {{
            color: {sidebar_text_final} !important;
            -webkit-text-fill-color: {sidebar_text_final} !important;
            opacity: 1 !important;
        }}

        [data-testid="stFileUploaderFile"] svg {{
            color: {sidebar_text_final} !important;
            fill: {sidebar_text_final} !important;
            opacity: 1 !important;
        }}

        [data-testid="stFileUploaderFile"] button {{
            background: {"#2563EB" if tema_visual == "Escuro" else "#FFFFFF"} !important;
            color: {"#FFFFFF" if tema_visual == "Escuro" else "#0F172A"} !important;
            border: 1px solid {"#3B82F6" if tema_visual == "Escuro" else "#CBD5E1"} !important;
            border-radius: 8px !important;
        }}

        [data-testid="stFileUploaderFile"] button * {{
            color: {"#FFFFFF" if tema_visual == "Escuro" else "#0F172A"} !important;
            -webkit-text-fill-color: {"#FFFFFF" if tema_visual == "Escuro" else "#0F172A"} !important;
        }}

        /* Blocos st.code com nome dos arquivos */
        [data-testid="stCodeBlock"],
        [data-testid="stCodeBlock"] pre,
        [data-testid="stCodeBlock"] code {{
            background: {"#111827" if tema_visual == "Escuro" else "#F8FAFC"} !important;
            color: {sidebar_text_final} !important;
            -webkit-text-fill-color: {sidebar_text_final} !important;
            border-color: {sidebar_border_final} !important;
        }}

        /* Tabelas e dataframes coerentes com o tema */
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {{
            background: {"#111827" if tema_visual == "Escuro" else "#FFFFFF"} !important;
            border: 1px solid {sidebar_border_final} !important;
            border-radius: 10px !important;
        }}

        /* Fundo geral e conteúdo */
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"] {{
            background: {"#0F172A" if tema_visual == "Escuro" else "#F3F6FA"} !important;
            color: {sidebar_text_final} !important;
        }}

        /* Elimina a faixa branca no topo */
        header[data-testid="stHeader"],
        [data-testid="stHeader"],
        .stAppHeader,
        [data-testid="stToolbar"] {{
            background: {"#0F172A" if tema_visual == "Escuro" else "#F3F6FA"} !important;
            background-color: {"#0F172A" if tema_visual == "Escuro" else "#F3F6FA"} !important;
            box-shadow: none !important;
            border: none !important;
        }}

        [data-testid="stDecoration"] {{
            display: none !important;
        }}

        [data-testid="stMainBlockContainer"] {{
            padding-top: 1rem !important;
        }}

        [data-testid="stMainBlockContainer"] h1,
        [data-testid="stMainBlockContainer"] h2,
        [data-testid="stMainBlockContainer"] h3,
        [data-testid="stMainBlockContainer"] h4,
        [data-testid="stMainBlockContainer"] p,
        [data-testid="stMainBlockContainer"] span,
        [data-testid="stMainBlockContainer"] label {{
            color: {sidebar_text_final} !important;
        }}

        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] * {{
            color: {sidebar_muted_final} !important;
        }}

        /* Métricas nativas */
        [data-testid="stMetric"] {{
            background: {"#111827" if tema_visual == "Escuro" else "#FFFFFF"} !important;
            border: 1px solid {sidebar_border_final} !important;
            border-radius: 12px !important;
            padding: 14px !important;
            box-shadow: {"0 8px 18px rgba(0,0,0,.18)" if tema_visual == "Escuro" else "0 6px 14px rgba(15,23,42,.08)"} !important;
        }}

        [data-testid="stMetric"] label,
        [data-testid="stMetricValue"],
        [data-testid="stMetricDelta"] {{
            color: {sidebar_text_final} !important;
        }}

        /* Containers de gráficos */
        [data-testid="stPlotlyChart"],
        [data-testid="stVegaLiteChart"] {{
            background: {"#111827" if tema_visual == "Escuro" else "#FFFFFF"} !important;
            border: 1px solid {sidebar_border_final} !important;
            border-radius: 14px !important;
            padding: 8px !important;
        }}

        /* Cartões gerenciais */
        .td-card,
        .td-comparativo-card {{
            background: {"#111827" if tema_visual == "Escuro" else "#FFFFFF"} !important;
            color: {sidebar_text_final} !important;
            border-color: {sidebar_border_final} !important;
        }}

        .td-card *,
        .td-comparativo-card * {{
            color: inherit;
        }}

        /* Tabelas executivas clean */
        .td-clean-table-wrap {{
            background: {"#111827" if tema_visual == "Escuro" else "#FFFFFF"};
            border: 1px solid {sidebar_border_final};
            border-radius: 14px;
            overflow: auto;
            max-height: 520px;
            box-shadow: 0 3px 10px rgba(15,23,42,.06);
        }}

        .td-clean-table-wrap table {{
            width: 100%;
            border-collapse: collapse;
            color: {sidebar_text_final};
            font-size: 0.84rem;
        }}

        .td-clean-table-wrap thead th {{
            position: sticky;
            top: 0;
            z-index: 2;
            background: {"#1E293B" if tema_visual == "Escuro" else "#EAF2FF"} !important;
            color: {"#F8FAFC" if tema_visual == "Escuro" else "#0F172A"} !important;
            border-bottom: 1px solid {"#475569" if tema_visual == "Escuro" else "#BFDBFE"} !important;
            padding: 10px 12px !important;
            text-align: left !important;
            font-weight: 800 !important;
            white-space: nowrap;
        }}

        .td-clean-table-wrap tbody td,
        .td-clean-table-wrap tbody th {{
            background: {"#111827" if tema_visual == "Escuro" else "#FFFFFF"};
            color: {sidebar_text_final};
            border-bottom: 1px solid {"#243044" if tema_visual == "Escuro" else "#E2E8F0"};
            padding: 9px 12px;
            white-space: nowrap;
        }}

        .td-clean-table-wrap tbody tr:nth-child(even) td,
        .td-clean-table-wrap tbody tr:nth-child(even) th {{
            background: {"#17223A" if tema_visual == "Escuro" else "#F8FAFC"};
        }}

        .td-clean-table-wrap tbody tr:hover td,
        .td-clean-table-wrap tbody tr:hover th {{
            box-shadow:
                inset 0 1px 0 {"#475569" if tema_visual == "Escuro" else "#BFDBFE"},
                inset 0 -1px 0 {"#475569" if tema_visual == "Escuro" else "#BFDBFE"};
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# Padroniza todos os gráficos Plotly conforme o tema escolhido.
if not hasattr(st, "_td_original_plotly_chart"):
    st._td_original_plotly_chart = st.plotly_chart

def _plotly_chart_com_tema(fig, *args, **kwargs):
    try:
        if tema_visual == "Escuro":
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#111827",
                plot_bgcolor="#111827",
                font=dict(color="#F8FAFC"),
                title_font=dict(color="#F8FAFC"),
                legend=dict(
                    font=dict(color="#F8FAFC"),
                    bgcolor="rgba(0,0,0,0)",
                ),
                margin=dict(l=45, r=30, t=55, b=45),
            )
            fig.update_xaxes(
                color="#CBD5E1",
                gridcolor="#334155",
                zerolinecolor="#475569",
                title_font=dict(color="#CBD5E1"),
                tickfont=dict(color="#CBD5E1"),
            )
            fig.update_yaxes(
                color="#CBD5E1",
                gridcolor="#334155",
                zerolinecolor="#475569",
                title_font=dict(color="#CBD5E1"),
                tickfont=dict(color="#CBD5E1"),
            )
        else:
            fig.update_layout(
                template="plotly_white",
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                font=dict(color="#0F172A"),
                title_font=dict(color="#0F172A"),
                legend=dict(
                    font=dict(color="#0F172A"),
                    bgcolor="rgba(0,0,0,0)",
                ),
                margin=dict(l=45, r=30, t=55, b=45),
            )
            fig.update_xaxes(
                color="#475569",
                gridcolor="#E2E8F0",
                zerolinecolor="#CBD5E1",
                title_font=dict(color="#475569"),
                tickfont=dict(color="#475569"),
            )
            fig.update_yaxes(
                color="#475569",
                gridcolor="#E2E8F0",
                zerolinecolor="#CBD5E1",
                title_font=dict(color="#475569"),
                tickfont=dict(color="#475569"),
            )
    except Exception:
        pass

    return st._td_original_plotly_chart(fig, *args, **kwargs)

st.plotly_chart = _plotly_chart_com_tema

# Renderização clean das tabelas nos dois temas.
if not hasattr(st, "_td_original_dataframe"):
    st._td_original_dataframe = st.dataframe

def _dataframe_com_tema(data=None, *args, **kwargs):
    try:
        if isinstance(data, pd.DataFrame):
            tabela_html = data.to_html(
                classes="td-clean-table",
                index=False,
                border=0,
                escape=True,
            )
            return st.markdown(
                f'<div class="td-clean-table-wrap">{tabela_html}</div>',
                unsafe_allow_html=True,
            )

        # Preserva as cores e destaques dos objetos pandas Styler,
        # ocultando sempre o índice visual.
        if hasattr(data, "to_html") and data.__class__.__name__ == "Styler":
            try:
                data = data.hide(axis="index")
            except Exception:
                pass

            tabela_html = data.to_html()
            return st.markdown(
                f'<div class="td-clean-table-wrap">{tabela_html}</div>',
                unsafe_allow_html=True,
            )
    except Exception:
        pass

    return st._td_original_dataframe(data, *args, **kwargs)

st.dataframe = _dataframe_com_tema



# ==================================================
# EXECUTIVO SEM PDF ANTIGO
# ==================================================

def exibir_executivo_sem_pdf_antigo(*args, **kwargs):
    """
    Exibe a página Executivo mantendo os indicadores e gráficos,
    mas bloqueia a geração antiga de PDF. O relatório oficial fica
    disponível exclusivamente no menu Relatório.
    """

    botao_original = st.button
    download_original = st.download_button
    subheader_original = st.subheader
    caption_original = st.caption
    markdown_original = st.markdown
    write_original = st.write

    def _texto_label(args_local, kwargs_local):
        if args_local:
            return str(args_local[0])
        return str(kwargs_local.get("label", ""))

    def botao_filtrado(*args_local, **kwargs_local):
        label = _texto_label(args_local, kwargs_local).lower()

        if (
            "relatório executivo" in label
            or "relatorio executivo" in label
            or "gerar relatório" in label
            or "gerar relatorio" in label
        ):
            return False

        return botao_original(*args_local, **kwargs_local)

    def download_filtrado(*args_local, **kwargs_local):
        label = _texto_label(args_local, kwargs_local).lower()

        if (
            "relatório executivo" in label
            or "relatorio executivo" in label
            or "baixar relatório" in label
            or "baixar relatorio" in label
        ):
            return False

        return download_original(*args_local, **kwargs_local)

    def subheader_filtrado(*args_local, **kwargs_local):
        texto_subheader = _texto_label(
            args_local,
            kwargs_local,
        ).strip().lower()

        if texto_subheader in {
            "relatório executivo",
            "relatorio executivo",
        }:
            return None

        return subheader_original(*args_local, **kwargs_local)

    def caption_filtrado(*args_local, **kwargs_local):
        texto_caption = _texto_label(
            args_local,
            kwargs_local,
        ).strip().lower()

        if (
            "gere o pdf" in texto_caption
            or "gerar o pdf" in texto_caption
            or "relatório executivo" in texto_caption
            or "relatorio executivo" in texto_caption
        ):
            return None

        return caption_original(*args_local, **kwargs_local)

    def markdown_filtrado(*args_local, **kwargs_local):
        conteudo = _texto_label(
            args_local,
            kwargs_local,
        ).strip().lower()

        if (
            "relatório executivo" in conteudo
            or "relatorio executivo" in conteudo
            or "gere o pdf com os principais indicadores" in conteudo
            or "gerar o pdf com os principais indicadores" in conteudo
        ):
            return None

        return markdown_original(*args_local, **kwargs_local)

    def write_filtrado(*args_local, **kwargs_local):
        conteudo = _texto_label(
            args_local,
            kwargs_local,
        ).strip().lower()

        if (
            "relatório executivo" in conteudo
            or "relatorio executivo" in conteudo
            or "gere o pdf com os principais indicadores" in conteudo
            or "gerar o pdf com os principais indicadores" in conteudo
        ):
            return None

        return write_original(*args_local, **kwargs_local)

    try:
        st.button = botao_filtrado
        st.download_button = download_filtrado
        st.subheader = subheader_filtrado
        st.caption = caption_filtrado
        st.markdown = markdown_filtrado
        st.write = write_filtrado

        return exibir_executivo(*args, **kwargs)

    finally:
        st.button = botao_original
        st.download_button = download_original
        st.subheader = subheader_original
        st.caption = caption_original
        st.markdown = markdown_original
        st.write = write_original


# ==================================================
# CARDS PADRONIZADOS PARA CLARO E ESCURO
# ==================================================

def _formatar_numero_br(valor, casas=0):
    try:
        numero = float(valor)
        texto = f"{numero:,.{casas}f}"
        return texto.replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(valor)


def _valor_principal(args, kwargs):
    for valor in args:
        if isinstance(valor, (int, float)):
            return valor

    for valor in kwargs.values():
        if isinstance(valor, (int, float)):
            return valor

    return args[0] if args else "—"


def _render_card_padrao(titulo, valor, icone, tipo="numero", destaque="#2563EB"):
    if tipo == "moeda":
        valor_formatado = f"R$ {_formatar_numero_br(valor, 2)}"
    elif tipo == "percentual":
        valor_formatado = f"{_formatar_numero_br(valor, 2)}%"
    else:
        valor_formatado = _formatar_numero_br(valor, 0)

    fundo_card = "#111827" if tema_visual == "Escuro" else "#FFFFFF"
    texto_card = "#F8FAFC" if tema_visual == "Escuro" else "#0F172A"
    texto_secundario = "#CBD5E1" if tema_visual == "Escuro" else "#64748B"
    borda_card = "#334155" if tema_visual == "Escuro" else "#CBD5E1"

    html = (
        f'<div style="background:{fundo_card};'
        f'border:1px solid {borda_card};'
        f'border-top:3px solid {destaque};'
        f'border-radius:14px;padding:16px 18px;'
        f'min-height:112px;box-shadow:0 8px 20px rgba(15,23,42,.10);">'
        f'<div style="display:flex;justify-content:space-between;'
        f'align-items:center;margin-bottom:13px;">'
        f'<span style="font-size:12px;font-weight:750;'
        f'color:{texto_secundario};">{titulo}</span>'
        f'<span style="font-size:19px;">{icone}</span>'
        f'</div>'
        f'<div style="font-size:25px;line-height:1.1;font-weight:900;'
        f'color:{texto_card};">{valor_formatado}</div>'
        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)


def card_imoveis_totais(*args, **kwargs):
    _render_card_padrao(
        "Imóveis totais",
        _valor_principal(args, kwargs),
        "🏢",
        destaque="#2563EB",
    )


def card_imoveis_ocupados(*args, **kwargs):
    _render_card_padrao(
        "Imóveis ocupados",
        _valor_principal(args, kwargs),
        "✅",
        destaque="#22C55E",
    )


def card_imoveis_vagos(*args, **kwargs):
    _render_card_padrao(
        "Imóveis vagos",
        _valor_principal(args, kwargs),
        "🚪",
        destaque="#EF4444",
    )


def card_vacancia(*args, **kwargs):
    _render_card_padrao(
        "Vacância",
        _valor_principal(args, kwargs),
        "📉",
        tipo="percentual",
        destaque="#F59E0B",
    )


def card_ticket_medio(*args, **kwargs):
    _render_card_padrao(
        "Ticket médio",
        _valor_principal(args, kwargs),
        "💰",
        tipo="moeda",
        destaque="#06B6D4",
    )


def card_receita_total(*args, **kwargs):
    _render_card_padrao(
        "Receita total",
        _valor_principal(args, kwargs),
        "💵",
        tipo="moeda",
        destaque="#22C55E",
    )


def card_inadimplencia_imob(*args, **kwargs):
    _render_card_padrao(
        "Inadimplência",
        _valor_principal(args, kwargs),
        "⚠️",
        tipo="moeda",
        destaque="#EF4444",
    )


def card_contratos(*args, **kwargs):
    _render_card_padrao(
        "Contratos ativos",
        _valor_principal(args, kwargs),
        "📄",
        destaque="#2563EB",
    )


def card_contratos_vencendo(*args, **kwargs):
    _render_card_padrao(
        "Contratos vencendo",
        _valor_principal(args, kwargs),
        "📅",
        destaque="#F59E0B",
    )


def card_total_contratos(*args, **kwargs):
    _render_card_padrao(
        "Total de contratos",
        _valor_principal(args, kwargs),
        "📊",
        destaque="#2563EB",
    )


def card_contratos_ativos(*args, **kwargs):
    _render_card_padrao(
        "Contratos ativos",
        _valor_principal(args, kwargs),
        "📄",
        destaque="#22C55E",
    )


def card_valor_medio_contrato(*args, **kwargs):
    _render_card_padrao(
        "Valor médio",
        _valor_principal(args, kwargs),
        "💰",
        tipo="moeda",
        destaque="#06B6D4",
    )


# ==================================================
# UPLOAD
# ==================================================

# A base do cliente é publicada pelo administrador.
# O cliente não visualiza nem utiliza campo de upload.
from pathlib import Path as _PathCliente
from io import BytesIO as _BytesIOCliente

_candidatos_base_cliente = [
    _PathCliente("dados_cliente/Base_Imobiliaria.xlsx"),
    _PathCliente("upload/Base_Imobiliaria.xlsx"),
    _PathCliente("Base_Imobiliaria.xlsx"),
]

_caminho_base_cliente = next(
    (caminho for caminho in _candidatos_base_cliente if caminho.exists()),
    None,
)

arquivo = None

if _caminho_base_cliente is None:
    st.info(
        "A base deste cliente ainda não foi publicada pelo administrador."
    )
else:
    arquivo = _BytesIOCliente(_caminho_base_cliente.read_bytes())
    arquivo.name = _caminho_base_cliente.name
    st.success("Dados atualizados e disponíveis para consulta.")


# ==================================================
# CONTRATOS PRIORITÁRIOS — IMPACTO FINANCEIRO
# ==================================================

def _normalizar_chave_contrato(valor):
    texto = str(valor or "").strip().lower()
    substituicoes = {
        "á": "a", "à": "a", "ã": "a", "â": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for origem, destino in substituicoes.items():
        texto = texto.replace(origem, destino)
    return re.sub(r"[^a-z0-9]+", "_", texto).strip("_")


def _localizar_coluna_contrato(df, candidatos):
    mapa = {
        _normalizar_chave_contrato(coluna): coluna
        for coluna in df.columns
    }

    for candidato in candidatos:
        chave = _normalizar_chave_contrato(candidato)
        if chave in mapa:
            return mapa[chave]

    for chave_coluna, coluna_original in mapa.items():
        for candidato in candidatos:
            chave_candidato = _normalizar_chave_contrato(candidato)
            if chave_candidato in chave_coluna:
                return coluna_original

    return None


def _moeda_br_contrato(valor):
    try:
        texto = f"{float(valor):,.2f}"
        texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {texto}"
    except Exception:
        return "R$ 0,00"


def preparar_contratos_prioritarios(df_contratos):
    if df_contratos is None or len(df_contratos) == 0:
        return pd.DataFrame(), {
            "quantidade": 0,
            "valor_mensal": 0.0,
            "criticos": 0,
            "altos": 0,
        }

    df = df_contratos.copy()

    coluna_vencimento = _localizar_coluna_contrato(
        df,
        [
            "Data_Fim", "Data Final", "Data_Vencimento",
            "Vencimento", "Fim_Contrato", "Data de término",
            "Data_Termino", "Termino",
        ],
    )
    coluna_valor = _localizar_coluna_contrato(
        df,
        [
            "Valor_Aluguel", "Valor", "Valor_Contrato",
            "Aluguel", "Valor Mensal", "Receita",
        ],
    )
    coluna_cliente = _localizar_coluna_contrato(
        df,
        [
            "Cliente", "Locatario", "Locatário",
            "Inquilino", "Nome_Cliente",
        ],
    )
    coluna_imovel = _localizar_coluna_contrato(
        df,
        [
            "ID_Imovel", "Imovel", "Imóvel",
            "Codigo_Imovel", "Código do imóvel",
        ],
    )
    coluna_contrato = _localizar_coluna_contrato(
        df,
        [
            "ID_Contrato", "Contrato", "Codigo_Contrato",
            "Código do contrato",
        ],
    )
    coluna_status = _localizar_coluna_contrato(
        df,
        ["Status", "Situacao", "Situação", "Status_Contrato"],
    )

    if coluna_vencimento is None:
        return pd.DataFrame(), {
            "quantidade": 0,
            "valor_mensal": 0.0,
            "criticos": 0,
            "altos": 0,
            "aviso": (
                "A base de contratos não possui uma coluna de vencimento "
                "reconhecível."
            ),
        }

    df["_vencimento"] = pd.to_datetime(
        df[coluna_vencimento],
        errors="coerce",
        dayfirst=True,
    )
    hoje = pd.Timestamp.today().normalize()
    df["_dias"] = (df["_vencimento"] - hoje).dt.days

    if coluna_status is not None:
        status_normalizado = (
            df[coluna_status]
            .astype(str)
            .map(_normalizar_chave_contrato)
        )
        mascara_ativo = ~status_normalizado.str.contains(
            "cancel|encerr|inativ|rescind",
            na=False,
        )
        df = df[mascara_ativo].copy()

    # Considera vencidos recentes e contratos que vencem em até 90 dias.
    df = df[
        df["_dias"].notna()
        & (df["_dias"] >= -30)
        & (df["_dias"] <= 90)
    ].copy()

    if coluna_valor is not None:
        df["_valor"] = pd.to_numeric(
            df[coluna_valor],
            errors="coerce",
        ).fillna(0.0)
    else:
        df["_valor"] = 0.0

    def classificar_prioridade(dias):
        if dias < 0:
            return "CRÍTICA"
        if dias <= 15:
            return "CRÍTICA"
        if dias <= 30:
            return "ALTA"
        if dias <= 60:
            return "MÉDIA"
        return "MONITORAR"

    df["Prioridade"] = df["_dias"].map(classificar_prioridade)

    ordem_prioridade = {
        "CRÍTICA": 1,
        "ALTA": 2,
        "MÉDIA": 3,
        "MONITORAR": 4,
    }
    df["_ordem"] = df["Prioridade"].map(ordem_prioridade).fillna(9)

    df = df.sort_values(
        ["_ordem", "_valor", "_dias"],
        ascending=[True, False, True],
    )

    def texto_prazo(dias):
        dias = int(dias)
        if dias < 0:
            quantidade = abs(dias)
            return (
                "Vencido há 1 dia"
                if quantidade == 1
                else f"Vencido há {quantidade} dias"
            )
        if dias == 0:
            return "Vence hoje"
        if dias == 1:
            return "Falta 1 dia"
        return f"Faltam {dias} dias"

    saida = pd.DataFrame({
        "Prioridade": df["Prioridade"],
        "Contrato": (
            df[coluna_contrato].astype(str)
            if coluna_contrato is not None
            else "Não informado"
        ),
        "Imóvel": (
            df[coluna_imovel].astype(str)
            if coluna_imovel is not None
            else "Não informado"
        ),
        "Cliente": (
            df[coluna_cliente].astype(str)
            if coluna_cliente is not None
            else "Não informado"
        ),
        "Vencimento": df["_vencimento"].dt.strftime("%d/%m/%Y"),
        "Prazo": df["_dias"].map(texto_prazo),
        "_dias_num": df["_dias"].astype(int),
        "Valor mensal": df["_valor"].map(_moeda_br_contrato),
        "_valor_num": df["_valor"],
    })

    resumo = {
        "quantidade": int(len(saida)),
        "valor_mensal": float(saida["_valor_num"].sum()),
        "criticos": int((saida["Prioridade"] == "CRÍTICA").sum()),
        "altos": int((saida["Prioridade"] == "ALTA").sum()),
    }

    return saida, resumo


def exibir_contratos_prioritarios(df_contratos):
    st.markdown("### Contratos que exigem ação")
    st.caption(
        "Prioridade calculada pelo prazo até o vencimento e pelo valor "
        "mensal envolvido."
    )

    tabela, resumo = preparar_contratos_prioritarios(df_contratos)

    if tabela.empty:
        st.info(
            resumo.get(
                "aviso",
                "Nenhum contrato ativo vencido recentemente ou com "
                "vencimento nos próximos 90 dias foi identificado.",
            )
        )
        return

    qtd_vencidos = int((tabela["_dias_num"] < 0).sum())
    qtd_hoje = int((tabela["_dias_num"] == 0).sum())
    qtd_7_dias = int(((tabela["_dias_num"] > 0) & (tabela["_dias_num"] <= 7)).sum())
    principal = tabela.iloc[0]

    def card_resumo(titulo, valor, subtitulo, borda, fundo):
        st.markdown(
            f"""
            <div style="background:{fundo}; border:1px solid {borda}; border-left:6px solid {borda};
                        border-radius:14px; padding:14px 16px; min-height:110px; box-shadow:0 2px 8px rgba(15,23,42,0.05);">
                <div style="font-size:12px; font-weight:700; color:#475569; text-transform:uppercase; letter-spacing:0.4px;">{titulo}</div>
                <div style="font-size:22px; font-weight:800; color:#0F172A; margin-top:8px;">{valor}</div>
                <div style="font-size:13px; color:#334155; margin-top:8px;">{subtitulo}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        card_resumo(
            "Contratos em atenção",
            str(resumo["quantidade"]),
            "Total de contratos que exigem monitoramento.",
            "#2563EB",
            "#EFF6FF",
        )
    with col2:
        card_resumo(
            "Valor mensal envolvido",
            _moeda_br_contrato(resumo["valor_mensal"]),
            "Receita mensal impactada pelos contratos priorizados.",
            "#EA580C",
            "#FFF7ED",
        )
    with col3:
        card_resumo(
            "Prioridade crítica",
            str(resumo["criticos"]),
            f"{qtd_vencidos} vencido(s) e {qtd_hoje} vencendo hoje.",
            "#DC2626",
            "#FEF2F2",
        )
    with col4:
        card_resumo(
            "Próximos 7 dias",
            str(qtd_7_dias),
            "Contratos com vencimento muito próximo.",
            "#D97706",
            "#FFFBEB",
        )

    st.warning(
        "Ação imediata recomendada: contrato "
        f"{principal['Contrato']} | imóvel {principal['Imóvel']} | cliente {principal['Cliente']} | "
        f"{principal['Valor mensal']} por mês | {principal['Prazo']}."
    )

    tabela_exibicao = tabela.drop(columns=["_valor_num", "_dias_num"])
    corte_valor_alto = float(tabela["_valor_num"].quantile(0.75)) if not tabela.empty else 0.0

    def cor_prioridade(valor):
        mapa_cores = {
            "CRÍTICA": "background-color: #FEE2E2; color: #991B1B; font-weight: 800;",
            "ALTA": "background-color: #FEF3C7; color: #92400E; font-weight: 800;",
            "MÉDIA": "background-color: #DBEAFE; color: #1E3A8A; font-weight: 800;",
            "MONITORAR": "background-color: #DCFCE7; color: #166534; font-weight: 800;",
        }
        return mapa_cores.get(str(valor), "")

    def cor_linha(row):
        prioridade = str(row.get("Prioridade", ""))
        if prioridade == "CRÍTICA":
            cor = "#FFF7F7"
        elif prioridade == "ALTA":
            cor = "#FFFBEB"
        elif prioridade == "MÉDIA":
            cor = "#F8FAFC"
        else:
            cor = "#FFFFFF"
        return [f"background-color: {cor};" for _ in row]

    def cor_prazo(valor):
        texto = str(valor).strip().lower()
        numero = None
        achou = re.search(r"(\d+)", texto)
        if achou:
            numero = int(achou.group(1))

        if "vence hoje" in texto or "vencido" in texto:
            return "background-color: #FEE2E2; color: #991B1B; font-weight: 800;"
        if "faltam" in texto and numero is not None and numero <= 7:
            return "background-color: #FEF3C7; color: #92400E; font-weight: 800;"
        if "faltam" in texto and numero is not None and numero <= 15:
            return "background-color: #DBEAFE; color: #1E3A8A; font-weight: 700;"
        return "background-color: #ECFDF5; color: #166534; font-weight: 700;"

    def destaque_valor(valor):
        texto = str(valor)
        numero_texto = re.sub(r"[^0-9,.-]", "", texto)
        numero_texto = (
            numero_texto
            .replace(".", "")
            .replace(",", ".")
        )
        try:
            numero = float(numero_texto)
        except Exception:
            numero = 0.0

        if numero >= corte_valor_alto and corte_valor_alto > 0:
            return "background-color: #FFF7ED; color: #9A3412; font-weight: 800;"
        return "font-weight: 700; color: #0F172A;"

    tabela_estilizada = (
        tabela_exibicao.style
        .apply(cor_linha, axis=1)
        .applymap(cor_prioridade, subset=["Prioridade"])
        .applymap(cor_prazo, subset=["Prazo"])
        .applymap(destaque_valor, subset=["Valor mensal"])
        .set_properties(
            **{
                "color": "#0F172A",
                "border-color": "#E2E8F0",
            }
        )
        .set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [
                        ("background-color", "#DBEAFE"),
                        ("color", "#0F172A"),
                        ("font-weight", "800"),
                        ("border-color", "#BFDBFE"),
                    ],
                },
                {
                    "selector": "td",
                    "props": [
                        ("padding", "8px 10px"),
                    ],
                },
            ]
        )
    )

    st.dataframe(
        tabela_estilizada,
        use_container_width=True,
        hide_index=True,
        height=430,
        column_config={
            "Prioridade": st.column_config.NumberColumn(
                "Prioridade",
                width="small",
            ),
            "Tipo": st.column_config.TextColumn(
                "Tipo",
                width="small",
            ),
            "Identificação": st.column_config.TextColumn(
                "Identificação",
                width="small",
            ),
            "Local/Cliente": st.column_config.TextColumn(
                "Cliente / Local",
                width="medium",
            ),
            "Nível de risco": st.column_config.TextColumn(
                "Nível de risco",
                width="small",
            ),
            "Índice": st.column_config.NumberColumn(
                "Índice",
                width="small",
            ),
            "Impacto mensal": st.column_config.TextColumn(
                "Impacto mensal",
                width="medium",
            ),
            "Motivo": st.column_config.TextColumn(
                "Motivo",
                width="medium",
            ),
            "Ação recomendada": st.column_config.TextColumn(
                "Ação recomendada",
                width="large",
            ),
        },
    )



# ==================================================
# RECEITA EM RISCO — DIFERENCIAL EXECUTIVO
# ==================================================

def _numero_moeda_generico(valor):
    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor or "").strip()
    texto = re.sub(r"[^0-9,.-]", "", texto)
    texto = texto.replace(".", "").replace(",", ".")

    try:
        return float(texto)
    except Exception:
        return 0.0


def _localizar_coluna_generica(df, candidatos):
    if df is None or len(df.columns) == 0:
        return None

    mapa = {
        _normalizar_chave_contrato(coluna): coluna
        for coluna in df.columns
    }

    for candidato in candidatos:
        chave = _normalizar_chave_contrato(candidato)
        if chave in mapa:
            return mapa[chave]

    for chave_coluna, coluna_original in mapa.items():
        for candidato in candidatos:
            chave_candidato = _normalizar_chave_contrato(candidato)
            if chave_candidato and chave_candidato in chave_coluna:
                return coluna_original

    return None


def _top_imoveis_vagos_risco(df_imoveis, limite=5):
    if df_imoveis is None or len(df_imoveis) == 0:
        return pd.DataFrame()

    df = df_imoveis.copy()

    coluna_status = _localizar_coluna_generica(
        df,
        ["status", "situacao", "situação"],
    )
    coluna_valor = _localizar_coluna_generica(
        df,
        ["valor_aluguel", "valor aluguel", "aluguel", "valor"],
    )
    coluna_imovel = _localizar_coluna_generica(
        df,
        ["id_imovel", "imovel", "imóvel", "codigo_imovel"],
    )
    coluna_bairro = _localizar_coluna_generica(
        df,
        ["bairro"],
    )
    coluna_dias = _localizar_coluna_generica(
        df,
        ["dias_vagos", "dias vagos", "dias_vacancia"],
    )

    if coluna_status is None or coluna_valor is None:
        return pd.DataFrame()

    status = df[coluna_status].astype(str).map(_normalizar_chave_contrato)
    df = df[status.str.contains("vago", na=False)].copy()

    if df.empty:
        return pd.DataFrame()

    df["_valor"] = df[coluna_valor].map(_numero_moeda_generico)
    df["_dias"] = (
        pd.to_numeric(df[coluna_dias], errors="coerce").fillna(0)
        if coluna_dias is not None
        else 0
    )

    # Perda acumulada estimada: aluguel mensal proporcional aos dias vagos.
    df["_perda_acumulada"] = df["_valor"] * (df["_dias"] / 30)

    df = df.sort_values(
        ["_perda_acumulada", "_valor"],
        ascending=[False, False],
    ).head(limite)

    return pd.DataFrame({
        "Imóvel": (
            df[coluna_imovel].astype(str)
            if coluna_imovel is not None
            else "Não informado"
        ),
        "Bairro": (
            df[coluna_bairro].astype(str)
            if coluna_bairro is not None
            else "Não informado"
        ),
        "Dias vagos": df["_dias"].astype(int),
        "Aluguel mensal": df["_valor"],
        "Perda acumulada estimada": df["_perda_acumulada"],
    })


def exibir_receita_em_risco(
    df_imoveis,
    df_contratos,
    inadimplencia,
    receita_perdida,
):
    tabela_contratos, resumo_contratos = preparar_contratos_prioritarios(
        df_contratos
    )

    contratos_em_risco = float(
        resumo_contratos.get("valor_mensal", 0.0)
    )
    inadimplencia_valor = float(inadimplencia or 0.0)
    vacancia_valor = float(receita_perdida or 0.0)

    st.markdown("## Riscos e impactos financeiros")
    st.caption(
        "As frentes abaixo têm naturezas diferentes e, por isso, "
        "não devem ser somadas em um único total."
    )

    fundo_total = "#1E293B" if tema_visual == "Escuro" else "#EFF6FF"
    texto_total = "#DBEAFE" if tema_visual == "Escuro" else "#1E3A8A"
    borda_total = "#3B82F6"

    st.markdown(
        f"""
        <div style="
            background:{fundo_total};
            border:1px solid {borda_total};
            border-left:7px solid #2563EB;
            border-radius:16px;
            padding:18px 20px;
            margin-bottom:16px;
        ">
            <div style="
                font-size:12px;
                font-weight:800;
                text-transform:uppercase;
                letter-spacing:.6px;
                color:{texto_total};
            ">
                Panorama executivo
            </div>
            <div style="
                font-size:30px;
                font-weight:900;
                color:{texto_total};
                margin-top:7px;
            ">
                3 frentes financeiras exigem ação
            </div>
            <div style="
                margin-top:8px;
                font-size:13px;
                color:{texto_total};
            ">
                Inadimplência acumulada, perda mensal por vacância e receita mensal sob atenção contratual.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div style="
                background:{"#111827" if tema_visual == "Escuro" else "#FFFFFF"};
                border:1px solid {"#334155" if tema_visual == "Escuro" else "#FCA5A5"};
                border-top:5px solid #DC2626;
                border-radius:14px;
                padding:15px 16px;
                min-height:118px;
            ">
                <div style="font-size:12px;font-weight:800;color:{sidebar_muted_final};">
                    INADIMPLÊNCIA
                </div>
                <div style="font-size:24px;font-weight:900;color:#DC2626;margin-top:9px;">
                    {_moeda_br_contrato(inadimplencia_valor)}
                </div>
                <div style="font-size:13px;color:{sidebar_muted_final};margin-top:8px;">
                    Saldo acumulado já vencido e ainda não recebido.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div style="
                background:{"#111827" if tema_visual == "Escuro" else "#FFFFFF"};
                border:1px solid {"#334155" if tema_visual == "Escuro" else "#FDBA74"};
                border-top:5px solid #EA580C;
                border-radius:14px;
                padding:15px 16px;
                min-height:118px;
            ">
                <div style="font-size:12px;font-weight:800;color:{sidebar_muted_final};">
                    VACÂNCIA
                </div>
                <div style="font-size:24px;font-weight:900;color:#EA580C;margin-top:9px;">
                    {_moeda_br_contrato(vacancia_valor)}
                </div>
                <div style="font-size:13px;color:{sidebar_muted_final};margin-top:8px;">
                    Perda estimada por mês com imóveis vagos.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div style="
                background:{"#111827" if tema_visual == "Escuro" else "#FFFFFF"};
                border:1px solid {"#334155" if tema_visual == "Escuro" else "#FDE68A"};
                border-top:5px solid #D97706;
                border-radius:14px;
                padding:15px 16px;
                min-height:118px;
            ">
                <div style="font-size:12px;font-weight:800;color:{sidebar_muted_final};">
                    CONTRATOS EM ATENÇÃO
                </div>
                <div style="font-size:24px;font-weight:900;color:#D97706;margin-top:9px;">
                    {_moeda_br_contrato(contratos_em_risco)}
                </div>
                <div style="font-size:13px;color:{sidebar_muted_final};margin-top:8px;">
                    Receita mensal vinculada a contratos vencidos ou próximos do vencimento.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Onde agir primeiro")

    top_vagos = _top_imoveis_vagos_risco(df_imoveis, limite=5)

    col_vagos, col_contratos = st.columns(2)

    with col_vagos:
        st.markdown("#### Imóveis com maior perda acumulada")

        if top_vagos.empty:
            st.info("Nenhum imóvel vago com valor reconhecível foi encontrado.")
        else:
            tabela_vagos = top_vagos.copy()
            tabela_vagos["Aluguel mensal"] = tabela_vagos[
                "Aluguel mensal"
            ].map(_moeda_br_contrato)
            tabela_vagos["Perda acumulada estimada"] = tabela_vagos[
                "Perda acumulada estimada"
            ].map(_moeda_br_contrato)

            st.dataframe(
                tabela_vagos,
                use_container_width=True,
                hide_index=True,
            )

    with col_contratos:
        st.markdown("#### Contratos com maior valor exposto")

        if tabela_contratos.empty:
            st.info("Nenhum contrato em atenção foi identificado.")
        else:
            top_contratos = (
                tabela_contratos
                .sort_values("_valor_num", ascending=False)
                .head(5)
                .drop(columns=["_valor_num", "_dias_num"])
            )

            st.dataframe(
                top_contratos,
                use_container_width=True,
                hide_index=True,
            )

    if not top_vagos.empty:
        principal_vago = top_vagos.iloc[0]
        st.warning(
            "Prioridade sugerida: atuar primeiro no imóvel "
            f"{principal_vago['Imóvel']} ({principal_vago['Bairro']}), "
            f"com {int(principal_vago['Dias vagos'])} dias vagos e "
            f"perda acumulada estimada de "
            f"{_moeda_br_contrato(principal_vago['Perda acumulada estimada'])}."
        )

    st.caption(
        "Leitura correta: inadimplência é saldo acumulado; vacância e "
        "contratos em atenção representam impacto mensal. Como podem existir "
        "sobreposições entre as frentes, os valores são apresentados "
        "separadamente."
    )



# ==================================================
# ÍNDICE DE RISCO POR IMÓVEL
# ==================================================

def calcular_indice_risco_imoveis(df_imoveis):
    if df_imoveis is None or len(df_imoveis) == 0:
        return pd.DataFrame()

    df = df_imoveis.copy()

    coluna_status = _localizar_coluna_generica(
        df,
        ["status", "situacao", "situação"],
    )
    coluna_valor = _localizar_coluna_generica(
        df,
        ["valor_aluguel", "valor aluguel", "aluguel", "valor"],
    )
    coluna_imovel = _localizar_coluna_generica(
        df,
        ["id_imovel", "imovel", "imóvel", "codigo_imovel"],
    )
    coluna_bairro = _localizar_coluna_generica(
        df,
        ["bairro"],
    )
    coluna_dias = _localizar_coluna_generica(
        df,
        ["dias_vagos", "dias vagos", "dias_vacancia"],
    )
    coluna_tipo = _localizar_coluna_generica(
        df,
        ["tipo_imovel", "tipo imóvel", "tipo"],
    )

    if coluna_status is None:
        return pd.DataFrame()

    status_normalizado = (
        df[coluna_status]
        .astype(str)
        .map(_normalizar_chave_contrato)
    )

    df["_vago"] = status_normalizado.str.contains("vago", na=False)
    df["_valor"] = (
        df[coluna_valor].map(_numero_moeda_generico)
        if coluna_valor is not None
        else 0.0
    )
    df["_dias"] = (
        pd.to_numeric(df[coluna_dias], errors="coerce").fillna(0)
        if coluna_dias is not None
        else 0
    )

    valores_vagos = df.loc[df["_vago"], "_valor"]
    referencia_valor = (
        float(valores_vagos.quantile(0.75))
        if len(valores_vagos) > 0
        else 0.0
    )

    def pontuar_linha(linha):
        if not bool(linha["_vago"]):
            return 5

        dias = max(float(linha["_dias"]), 0.0)
        valor = max(float(linha["_valor"]), 0.0)

        pontos_status = 35
        pontos_dias = min((dias / 120.0) * 40.0, 40.0)

        if referencia_valor > 0:
            pontos_valor = min(
                (valor / referencia_valor) * 25.0,
                25.0,
            )
        else:
            pontos_valor = 0.0

        return round(
            min(
                pontos_status + pontos_dias + pontos_valor,
                100,
            )
        )

    df["Índice de risco"] = df.apply(
        pontuar_linha,
        axis=1,
    )

    def classificar_risco(indice):
        if indice >= 70:
            return "CRÍTICO"
        if indice >= 40:
            return "ATENÇÃO"
        return "SAUDÁVEL"

    df["Classificação"] = df["Índice de risco"].map(
        classificar_risco
    )

    def motivo_linha(linha):
        if not bool(linha["_vago"]):
            return "Imóvel ocupado"

        dias = int(linha["_dias"])
        valor = float(linha["_valor"])

        motivos = []

        if dias >= 90:
            motivos.append("vacância acima de 90 dias")
        elif dias >= 30:
            motivos.append("vacância prolongada")
        else:
            motivos.append("imóvel vago")

        if referencia_valor > 0 and valor >= referencia_valor:
            motivos.append("aluguel de alto impacto")

        return " + ".join(motivos)

    df["Principal motivo"] = df.apply(
        motivo_linha,
        axis=1,
    )

    df["Perda acumulada estimada"] = (
        df["_valor"] * (df["_dias"] / 30)
    ).where(df["_vago"], 0.0)

    saida = pd.DataFrame({
        "Classificação": df["Classificação"],
        "Índice de risco": df["Índice de risco"],
        "Imóvel": (
            df[coluna_imovel].astype(str)
            if coluna_imovel is not None
            else "Não informado"
        ),
        "Bairro": (
            df[coluna_bairro].astype(str)
            if coluna_bairro is not None
            else "Não informado"
        ),
        "Tipo": (
            df[coluna_tipo].astype(str)
            if coluna_tipo is not None
            else "Não informado"
        ),
        "Status": df[coluna_status].astype(str),
        "Dias vagos": df["_dias"].astype(int),
        "Aluguel mensal": df["_valor"],
        "Perda acumulada estimada": df[
            "Perda acumulada estimada"
        ],
        "Principal motivo": df["Principal motivo"],
    })

    ordem = {
        "CRÍTICO": 1,
        "ATENÇÃO": 2,
        "SAUDÁVEL": 3,
    }

    saida["_ordem"] = saida["Classificação"].map(
        ordem
    ).fillna(9)

    return saida.sort_values(
        [
            "_ordem",
            "Índice de risco",
            "Perda acumulada estimada",
        ],
        ascending=[True, False, False],
    )


def exibir_indice_risco_imoveis(df_imoveis):
    tabela = calcular_indice_risco_imoveis(
        df_imoveis
    )

    st.divider()
    st.markdown("## Índice de risco por imóvel")
    st.caption(
        "Classificação gerencial baseada em status, dias vagos, "
        "valor do aluguel e impacto financeiro estimado."
    )

    if tabela.empty:
        st.info(
            "Não foi possível calcular o índice de risco com as "
            "colunas disponíveis na base."
        )
        return

    criticos = int(
        (tabela["Classificação"] == "CRÍTICO").sum()
    )
    atencao = int(
        (tabela["Classificação"] == "ATENÇÃO").sum()
    )
    saudaveis = int(
        (tabela["Classificação"] == "SAUDÁVEL").sum()
    )

    receita_critica = float(
        tabela.loc[
            tabela["Classificação"] == "CRÍTICO",
            "Aluguel mensal",
        ].sum()
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Imóveis críticos",
            criticos,
        )

    with col2:
        st.metric(
            "Imóveis em atenção",
            atencao,
        )

    with col3:
        st.metric(
            "Imóveis saudáveis",
            saudaveis,
        )

    with col4:
        st.metric(
            "Receita mensal crítica",
            _moeda_br_contrato(receita_critica),
        )

    tabela_exibicao = tabela.drop(
        columns=["_ordem"]
    ).copy()

    tabela_exibicao["Aluguel mensal"] = tabela_exibicao[
        "Aluguel mensal"
    ].map(_moeda_br_contrato)

    tabela_exibicao[
        "Perda acumulada estimada"
    ] = tabela_exibicao[
        "Perda acumulada estimada"
    ].map(_moeda_br_contrato)

    def cor_classificacao(valor):
        mapa = {
            "CRÍTICO": (
                "background-color: #FEE2E2; "
                "color: #991B1B; font-weight: 800;"
            ),
            "ATENÇÃO": (
                "background-color: #FEF3C7; "
                "color: #92400E; font-weight: 800;"
            ),
            "SAUDÁVEL": (
                "background-color: #DCFCE7; "
                "color: #166534; font-weight: 800;"
            ),
        }
        return mapa.get(str(valor), "")

    def cor_indice(valor):
        try:
            numero = float(valor)
        except Exception:
            numero = 0

        if numero >= 70:
            return (
                "background-color: #FEE2E2; "
                "color: #991B1B; font-weight: 800;"
            )
        if numero >= 40:
            return (
                "background-color: #FEF3C7; "
                "color: #92400E; font-weight: 800;"
            )
        return (
            "background-color: #DCFCE7; "
            "color: #166534; font-weight: 800;"
        )

    tabela_estilizada = (
        tabela_exibicao.style
        .applymap(
            cor_classificacao,
            subset=["Classificação"],
        )
        .applymap(
            cor_indice,
            subset=["Índice de risco"],
        )
    )

    st.dataframe(
        tabela_estilizada,
        use_container_width=True,
        hide_index=True,
    )

    principal = tabela.iloc[0]

    st.warning(
        "Prioridade do imóvel: "
        f"{principal['Imóvel']} | "
        f"{principal['Bairro']} | "
        f"índice {int(principal['Índice de risco'])}/100 | "
        f"{principal['Principal motivo']} | "
        f"perda acumulada estimada de "
        f"{_moeda_br_contrato(principal['Perda acumulada estimada'])}."
    )

    st.caption(
        "Metodologia atual: imóvel ocupado recebe risco mínimo. "
        "Imóveis vagos acumulam pontos por tempo de vacância e "
        "valor mensal do aluguel. O índice é gerencial e será "
        "refinado conforme novos dados forem incorporados."
    )



# ==================================================
# RANKING CONSOLIDADO DE PRIORIDADES
# ==================================================

def montar_ranking_prioridades(df_imoveis, df_contratos, limite=10):
    prioridades = []

    # Imóveis críticos e em atenção
    tabela_imoveis = calcular_indice_risco_imoveis(df_imoveis)

    if not tabela_imoveis.empty:
        candidatos_imoveis = tabela_imoveis[
            tabela_imoveis["Classificação"].isin(
                ["CRÍTICO", "ATENÇÃO"]
            )
        ].head(6)

        for _, linha in candidatos_imoveis.iterrows():
            indice = int(linha["Índice de risco"])
            classificacao = str(linha["Classificação"])
            impacto = float(linha["Aluguel mensal"])
            dias = int(linha["Dias vagos"])
            imovel = str(linha["Imóvel"])
            bairro = str(linha["Bairro"])
            motivo = str(linha["Principal motivo"])

            if dias >= 90:
                acao = (
                    "Revisar preço, divulgação e estratégia comercial "
                    "imediatamente."
                )
            elif dias >= 30:
                acao = (
                    "Intensificar divulgação e avaliar adequação do valor "
                    "do aluguel."
                )
            else:
                acao = (
                    "Acompanhar a vacância e acelerar a ocupação do imóvel."
                )

            prioridades.append(
                {
                    "Tipo": "Imóvel",
                    "Identificação": imovel,
                    "Local/Cliente": bairro,
                    "Nível": classificacao,
                    "Índice": indice,
                    "Impacto mensal": impacto,
                    "Motivo": motivo,
                    "Ação recomendada": acao,
                }
            )

    # Contratos críticos e de alta prioridade
    tabela_contratos, _ = preparar_contratos_prioritarios(
        df_contratos
    )

    if not tabela_contratos.empty:
        candidatos_contratos = tabela_contratos[
            tabela_contratos["Prioridade"].isin(
                ["CRÍTICA", "ALTA"]
            )
        ].head(6)

        for _, linha in candidatos_contratos.iterrows():
            prioridade = str(linha["Prioridade"])
            dias = int(linha["_dias_num"])
            impacto = float(linha["_valor_num"])
            contrato = str(linha["Contrato"])
            cliente = str(linha["Cliente"])
            imovel = str(linha["Imóvel"])
            prazo = str(linha["Prazo"])

            if dias < 0:
                indice = 100
                acao = (
                    "Regularizar vencimento e iniciar contato imediato "
                    "com o cliente."
                )
            elif dias == 0:
                indice = 98
                acao = (
                    "Confirmar renovação ou encerramento ainda hoje."
                )
            elif dias <= 7:
                indice = 95
                acao = (
                    "Iniciar tratativa de renovação imediatamente."
                )
            elif dias <= 15:
                indice = 90
                acao = (
                    "Agendar contato de renovação nesta semana."
                )
            else:
                indice = 80
                acao = (
                    "Preparar negociação e acompanhar a renovação."
                )

            prioridades.append(
                {
                    "Tipo": "Contrato",
                    "Identificação": contrato,
                    "Local/Cliente": f"{cliente} | {imovel}",
                    "Nível": prioridade,
                    "Índice": indice,
                    "Impacto mensal": impacto,
                    "Motivo": prazo,
                    "Ação recomendada": acao,
                }
            )

    if not prioridades:
        return pd.DataFrame()

    ranking = pd.DataFrame(prioridades)

    ordem_nivel = {
        "CRÍTICO": 1,
        "CRÍTICA": 1,
        "ALTA": 2,
        "ATENÇÃO": 3,
    }

    ranking["_ordem_nivel"] = ranking["Nível"].map(
        ordem_nivel
    ).fillna(9)

    ranking = ranking.sort_values(
        ["_ordem_nivel", "Índice", "Impacto mensal"],
        ascending=[True, False, False],
    ).head(limite).reset_index(drop=True)

    ranking.insert(
        0,
        "Prioridade",
        range(1, len(ranking) + 1),
    )

    return ranking


def exibir_ranking_prioridades(df_imoveis, df_contratos):
    ranking = montar_ranking_prioridades(
        df_imoveis,
        df_contratos,
        limite=10,
    )

    st.markdown("## Ranking de prioridades")
    st.caption(
        "Lista consolidada do que deve ser tratado primeiro, "
        "considerando risco, prazo e impacto financeiro."
    )

    if ranking.empty:
        st.info(
            "Nenhuma prioridade relevante foi identificada com os "
            "dados disponíveis."
        )
        return

    criticas = int(
        ranking["Nível"].isin(["CRÍTICO", "CRÍTICA"]).sum()
    )
    contratos = int(
        (ranking["Tipo"] == "Contrato").sum()
    )
    imoveis = int(
        (ranking["Tipo"] == "Imóvel").sum()
    )
    impacto_total = float(
        ranking["Impacto mensal"].sum()
    )

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Prioridades analisadas",
        len(ranking),
        help="Quantidade total de itens apresentados no ranking.",
    )
    col2.metric(
        "Composição do ranking",
        f"{contratos} contratos + {imoveis} imóveis",
        help="Tipos de itens que compõem as prioridades.",
    )
    col3.metric(
        "Impacto mensal monitorado",
        _moeda_br_contrato(impacto_total),
        help="Soma dos impactos mensais dos itens priorizados.",
    )

    st.info(
        "A tabela mistura contratos e imóveis em uma única ordem de atuação. "
        "O número 1 indica o item que deve ser tratado primeiro."
    )

    tabela = ranking.drop(
        columns=["_ordem_nivel"]
    ).copy()

    tabela["Nível"] = tabela["Nível"].map(
        lambda valor: (
            "CRÍTICO"
            if str(valor).upper() in {"CRÍTICO", "CRÍTICA"}
            else str(valor).upper()
        )
    )
    tabela = tabela.rename(
        columns={"Nível": "Nível de risco"}
    )

    tabela["Impacto mensal"] = tabela[
        "Impacto mensal"
    ].map(_moeda_br_contrato)

    def cor_nivel(valor):
        mapa = {
            "CRÍTICO": (
                "background-color:#FEE2E2;"
                "color:#991B1B;font-weight:800;"
            ),
            "CRÍTICA": (
                "background-color:#FEE2E2;"
                "color:#991B1B;font-weight:800;"
            ),
            "ALTA": (
                "background-color:#FEF3C7;"
                "color:#92400E;font-weight:800;"
            ),
            "ATENÇÃO": (
                "background-color:#DBEAFE;"
                "color:#1E3A8A;font-weight:800;"
            ),
        }
        return mapa.get(str(valor), "")

    def cor_prioridade(valor):
        try:
            numero = int(valor)
        except Exception:
            numero = 99

        if numero == 1:
            return (
                "background-color:#DC2626;"
                "color:#FFFFFF;font-weight:900;"
            )

        return "font-weight:800;"

    tabela_estilizada = (
        tabela.style
        .applymap(
            cor_nivel,
            subset=["Nível de risco"],
        )
        .applymap(
            cor_prioridade,
            subset=["Prioridade"],
        )
    )

    st.dataframe(
        tabela_estilizada,
        use_container_width=True,
        hide_index=True,
    )

    principal = ranking.iloc[0]

    st.warning(
        "Ação nº 1: "
        f"{principal['Tipo']} {principal['Identificação']} | "
        f"{principal['Motivo']} | "
        f"impacto mensal de "
        f"{_moeda_br_contrato(principal['Impacto mensal'])} | "
        f"{principal['Ação recomendada']}"
    )

    st.caption(
        "O ranking organiza as ações pela combinação de urgência, "
        "índice de risco e impacto mensal. Ele serve como ordem "
        "gerencial de atuação e não substitui análise jurídica ou "
        "contratual."
    )



# ==================================================
# PLANO DE AÇÃO DO MÊS
# ==================================================

def montar_plano_acao_mensal(df_imoveis, df_contratos, limite=8):
    ranking = montar_ranking_prioridades(
        df_imoveis,
        df_contratos,
        limite=limite,
    )

    if ranking.empty:
        return pd.DataFrame()

    linhas = []

    for _, linha in ranking.iterrows():
        tipo = str(linha["Tipo"])
        nivel = str(linha["Nível"])
        indice = int(linha["Índice"])
        impacto = float(linha["Impacto mensal"])
        motivo = str(linha["Motivo"])
        acao = str(linha["Ação recomendada"])
        identificacao = str(linha["Identificação"])
        local_cliente = str(linha["Local/Cliente"])

        if tipo == "Contrato":
            responsavel = "Gestão de contratos"
            if "Vencido" in motivo or "Vence hoje" in motivo:
                prazo = "Hoje"
            elif "Faltam" in motivo:
                try:
                    dias = int(re.search(r"(\d+)", motivo).group(1))
                except Exception:
                    dias = 30

                if dias <= 7:
                    prazo = "Até 2 dias"
                elif dias <= 15:
                    prazo = "Até 5 dias"
                else:
                    prazo = "Até 10 dias"
            else:
                prazo = "Até 10 dias"

            impacto_esperado = (
                "Proteger a receita mensal e reduzir risco de encerramento."
            )
        else:
            responsavel = "Comercial / Captação"
            if indice >= 90:
                prazo = "Até 3 dias"
            elif indice >= 70:
                prazo = "Até 7 dias"
            else:
                prazo = "Até 15 dias"

            impacto_esperado = (
                "Reduzir vacância e recuperar receita potencial."
            )

        status = "Não iniciado"

        linhas.append(
            {
                "Prioridade": int(linha["Prioridade"]),
                "Tipo": tipo,
                "Identificação": identificacao,
                "Local/Cliente": local_cliente,
                "Nível": nivel,
                "Ação": acao,
                "Responsável sugerido": responsavel,
                "Prazo recomendado": prazo,
                "Impacto mensal": impacto,
                "Impacto esperado": impacto_esperado,
                "Status": status,
            }
        )

    plano = pd.DataFrame(linhas)
    return plano.sort_values("Prioridade")


def exibir_plano_acao_mensal(df_imoveis, df_contratos):
    plano = montar_plano_acao_mensal(
        df_imoveis,
        df_contratos,
        limite=8,
    )

    st.markdown("## Plano de ação do mês")
    st.caption(
        "Transforma as prioridades do painel em tarefas objetivas, "
        "com responsável sugerido, prazo e impacto esperado."
    )

    if plano.empty:
        st.info(
            "Nenhuma ação prioritária foi identificada com os dados disponíveis."
        )
        return

    urgentes = int(
        plano["Prazo recomendado"].isin(
            ["Hoje", "Até 2 dias", "Até 3 dias"]
        ).sum()
    )
    contratos = int((plano["Tipo"] == "Contrato").sum())
    imoveis = int((plano["Tipo"] == "Imóvel").sum())
    impacto_total = float(plano["Impacto mensal"].sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ações prioritárias", len(plano))
    col2.metric("Ações urgentes", urgentes)
    col3.metric("Contratos / Imóveis", f"{contratos} / {imoveis}")
    col4.metric(
        "Impacto mensal relacionado",
        _moeda_br_contrato(impacto_total),
    )

    st.markdown("### Execução recomendada")

    tabela = plano.copy()

    # Versão compacta para leitura em zoom de 100%.
    tabela = tabela[
        [
            "Prioridade",
            "Tipo",
            "Identificação",
            "Local/Cliente",
            "Ação",
            "Responsável sugerido",
            "Prazo recomendado",
            "Impacto mensal",
            "Status",
        ]
    ].copy()

    tabela = tabela.rename(
        columns={
            "Responsável sugerido": "Responsável",
            "Prazo recomendado": "Prazo",
            "Impacto mensal": "Impacto",
            "Local/Cliente": "Cliente / Local",
        }
    )

    tabela["Impacto"] = tabela[
        "Impacto"
    ].map(_moeda_br_contrato)

    def cor_prazo(valor):
        texto = str(valor)

        if texto == "Hoje":
            return (
                "background-color:#FEE2E2;"
                "color:#991B1B;font-weight:800;"
            )
        if texto in {"Até 2 dias", "Até 3 dias"}:
            return (
                "background-color:#FEF3C7;"
                "color:#92400E;font-weight:800;"
            )
        if texto in {"Até 5 dias", "Até 7 dias"}:
            return (
                "background-color:#DBEAFE;"
                "color:#1E3A8A;font-weight:800;"
            )
        return (
            "background-color:#DCFCE7;"
            "color:#166534;font-weight:800;"
        )

    def cor_status(valor):
        texto = str(valor)

        if texto == "Não iniciado":
            return (
                "background-color:#F1F5F9;"
                "color:#475569;font-weight:800;"
            )
        if texto == "Em andamento":
            return (
                "background-color:#DBEAFE;"
                "color:#1E3A8A;font-weight:800;"
            )
        return (
            "background-color:#DCFCE7;"
            "color:#166534;font-weight:800;"
        )

    tabela_estilizada = (
        tabela.style
        .applymap(
            cor_prazo,
            subset=["Prazo"],
        )
        .applymap(
            cor_status,
            subset=["Status"],
        )
    )

    st.dataframe(
        tabela_estilizada,
        use_container_width=True,
        hide_index=True,
    )

    primeira = plano.iloc[0]

    st.warning(
        "Começar por: "
        f"{primeira['Tipo']} {primeira['Identificação']} | "
        f"{primeira['Ação']} | "
        f"responsável sugerido: {primeira['Responsável sugerido']} | "
        f"prazo: {primeira['Prazo recomendado']}."
    )

    st.caption(
        "O plano de ação organiza a execução do mês. O status será "
        "acompanhado em uma etapa posterior, quando incluirmos controle "
        "de andamento e conclusão."
    )



# ==================================================
# EXECUTIVO PREMIUM — COMPACTO E RESPONSIVO
# ==================================================

def _card_executivo_compacto(titulo, valor, subtitulo, cor):
    st.markdown(
        f"""
        <div class="td-exec-card" style="--td-accent:{cor};">
            <div class="td-exec-card-title">{titulo}</div>
            <div class="td-exec-card-value">{valor}</div>
            <div class="td-exec-card-subtitle">{subtitulo}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _figura_receita_bairros_compacta(receita_bairro):
    try:
        if isinstance(receita_bairro, pd.Series):
            dados = receita_bairro.reset_index()
            dados.columns = ["Bairro", "Receita"]
        elif isinstance(receita_bairro, pd.DataFrame):
            dados = receita_bairro.copy()

            coluna_bairro = _localizar_coluna_generica(
                dados,
                ["bairro"],
            )
            coluna_valor = _localizar_coluna_generica(
                dados,
                ["valor_aluguel", "receita", "valor"],
            )

            if coluna_bairro is None or coluna_valor is None:
                return None

            dados = (
                dados.groupby(coluna_bairro, as_index=False)[coluna_valor]
                .sum()
                .rename(
                    columns={
                        coluna_bairro: "Bairro",
                        coluna_valor: "Receita",
                    }
                )
            )
        else:
            return None

        dados["Receita"] = pd.to_numeric(
            dados["Receita"],
            errors="coerce",
        ).fillna(0)

        dados = dados.sort_values(
            "Receita",
            ascending=True,
        ).tail(8)

        figura = go.Figure(
            go.Bar(
                x=dados["Receita"],
                y=dados["Bairro"].astype(str),
                orientation="h",
                text=dados["Receita"].map(_moeda_br_contrato),
                textposition="outside",
                marker=dict(color="#2563EB"),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Receita: R$ %{x:,.2f}"
                    "<extra></extra>"
                ),
            )
        )
        figura.update_layout(
            title="Receita por bairro — Top 8",
            height=350,
            showlegend=False,
            xaxis_title="Receita potencial",
            yaxis_title="",
            margin=dict(l=20, r=40, t=55, b=30),
        )
        return figura
    except Exception:
        return None


def _figura_ocupacao_compacta(total_ocupados, total_vagos):
    figura = go.Figure(
        go.Pie(
            labels=["Ocupados", "Vagos"],
            values=[total_ocupados, total_vagos],
            hole=0.66,
            marker=dict(
                colors=["#2563EB", "#F97316"],
            ),
            textinfo="percent",
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Quantidade: %{value}<br>"
                "Participação: %{percent}"
                "<extra></extra>"
            ),
        )
    )

    figura.update_layout(
        title="Ocupação da carteira",
        height=350,
        margin=dict(l=20, r=20, t=55, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.08,
            xanchor="center",
            x=0.5,
        ),
    )
    return figura


def exibir_executivo_premium_compacto(
    receita,
    inadimplencia,
    vacancia,
    ticket,
    ativos,
    receita_perdida,
    perc_inadimplencia,
    eficiencia,
    score,
    classificacao,
    receita_bairro,
    total_ocupados,
    total_vagos,
    total_imoveis,
    df_imoveis,
    df_contratos,
):
    st.markdown(
        """
        <style>
            .td-exec-card {
                background: var(--secondary-background-color);
                border: 1px solid rgba(148,163,184,.35);
                border-top: 4px solid var(--td-accent);
                border-radius: 14px;
                padding: 14px 15px;
                min-height: 118px;
                box-shadow: 0 5px 14px rgba(15,23,42,.07);
                overflow: hidden;
            }

            .td-exec-card-title {
                font-size: 11px;
                font-weight: 800;
                letter-spacing: .45px;
                text-transform: uppercase;
                opacity: .72;
                white-space: normal;
            }

            .td-exec-card-value {
                font-size: clamp(20px, 1.65vw, 29px);
                line-height: 1.08;
                font-weight: 900;
                margin-top: 10px;
                overflow-wrap: anywhere;
            }

            .td-exec-card-subtitle {
                font-size: 12px;
                line-height: 1.35;
                margin-top: 8px;
                opacity: .72;
            }

            [data-testid="stMainBlockContainer"] {
                max-width: 100% !important;
                padding-left: clamp(.8rem, 2vw, 2.2rem) !important;
                padding-right: clamp(.8rem, 2vw, 2.2rem) !important;
            }

            [data-testid="stHorizontalBlock"] {
                gap: .75rem !important;
            }

            [data-testid="stTabs"] [data-baseweb="tab-list"] {
                overflow-x: auto !important;
                scrollbar-width: thin;
            }

            [data-testid="stTabs"] [role="tab"] {
                min-width: max-content !important;
                padding-left: 14px !important;
                padding-right: 14px !important;
            }

            [data-testid="stTabs"] [data-baseweb="tab-panel"] {
                padding-top: .85rem !important;
                margin-top: 0 !important;
            }

            [data-testid="stTabs"] [data-baseweb="tab-border"] {
                margin-bottom: 0 !important;
            }

            [data-testid="stTabs"] [role="tabpanel"] {
                padding-top: .85rem !important;
                margin-top: 0 !important;
            }

            [data-testid="stTabs"] [role="tabpanel"] > div {
                padding-top: 0 !important;
                margin-top: 0 !important;
            }

            [data-testid="stTabs"] [role="tabpanel"] > div > div:first-child {
                margin-top: 0 !important;
                padding-top: 0 !important;
            }

            [data-testid="stTabs"] h1,
            [data-testid="stTabs"] h2,
            [data-testid="stTabs"] h3 {
                margin-top: .35rem !important;
                padding-top: 0 !important;
            }

            [data-testid="stTabs"] hr {
                margin-top: .25rem !important;
                margin-bottom: .55rem !important;
            }

            @media (max-width: 1180px) {
                .td-exec-card {
                    min-height: 108px;
                    padding: 12px 13px;
                }

                .td-exec-card-value {
                    font-size: 21px;
                }

                [data-testid="stHorizontalBlock"] {
                    gap: .5rem !important;
                }
            }

            .td-clean-table-wrap {
                max-width: 100% !important;
                overflow-x: auto !important;
            }

            .td-clean-table-wrap table {
                min-width: 980px;
            }

            .td-clean-table-wrap th,
            .td-clean-table-wrap td {
                white-space: normal !important;
                vertical-align: top !important;
            }

            .td-clean-table-wrap th:nth-child(1),
            .td-clean-table-wrap td:nth-child(1) {
                width: 68px;
                text-align: center;
            }

            .td-clean-table-wrap th:nth-child(2),
            .td-clean-table-wrap td:nth-child(2) {
                width: 82px;
            }

            .td-clean-table-wrap th:nth-child(3),
            .td-clean-table-wrap td:nth-child(3) {
                width: 92px;
            }

            .td-clean-table-wrap th:nth-child(5),
            .td-clean-table-wrap td:nth-child(5) {
                min-width: 290px;
            }

            .td-clean-table-wrap th:nth-child(6),
            .td-clean-table-wrap td:nth-child(6) {
                min-width: 150px;
            }

            .td-clean-table-wrap th:nth-child(7),
            .td-clean-table-wrap td:nth-child(7) {
                width: 105px;
            }

            .td-clean-table-wrap th:nth-child(8),
            .td-clean-table-wrap td:nth-child(8) {
                width: 120px;
            }

            .td-clean-table-wrap th:nth-child(9),
            .td-clean-table-wrap td:nth-child(9) {
                width: 110px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## Painel executivo")
    st.caption(
        "Resumo gerencial compacto, organizado para leitura em zoom de 100%."
    )

    cards = st.columns(5)

    with cards[0]:
        _card_executivo_compacto(
            "Score",
            f"{float(score):.0f}/100",
            "Saúde geral da carteira",
            "#DC2626" if float(score) < 50 else "#F59E0B",
        )

    with cards[1]:
        _card_executivo_compacto(
            "Classificação",
            str(classificacao).replace("🔴", "").strip(),
            "Nível atual de atenção",
            "#DC2626",
        )

    with cards[2]:
        _card_executivo_compacto(
            "Receita contratada",
            _moeda_br_contrato(receita),
            "Base mensal da carteira",
            "#16A34A",
        )

    with cards[3]:
        _card_executivo_compacto(
            "Inadimplência",
            _moeda_br_contrato(inadimplencia),
            f"{float(perc_inadimplencia):.1f}% da receita".replace(".", ","),
            "#DC2626",
        )

    with cards[4]:
        _card_executivo_compacto(
            "Vacância",
            f"{float(vacancia):.1f}%".replace(".", ","),
            f"{int(total_vagos)} de {int(total_imoveis)} imóveis",
            "#EA580C",
        )

    st.markdown(
        """
        <div style="
            margin-top:8px;
            padding:9px 13px;
            border:1px solid rgba(148,163,184,.35);
            border-radius:10px;
            background:rgba(37,99,235,.05);
            font-size:12px;
            line-height:1.45;
        ">
            <strong>Como ler o score:</strong>
            0 a 49 = Crítico &nbsp;|&nbsp;
            50 a 79 = Atenção &nbsp;|&nbsp;
            80 a 100 = Saudável.
        </div>
        """,
        unsafe_allow_html=True,
    )

    classificacao_limpa = (
        str(classificacao)
        .replace("🔴", "")
        .replace("🟡", "")
        .replace("🟢", "")
        .strip()
    )

    principal_problema = (
        "inadimplência"
        if float(perc_inadimplencia) >= float(vacancia)
        else "vacância"
    )

    ranking_diagnostico = montar_ranking_prioridades(
        df_imoveis,
        df_contratos,
        limite=3,
    )
    risco_imoveis_diagnostico = calcular_indice_risco_imoveis(
        df_imoveis
    )
    contratos_diagnostico, resumo_contratos_diagnostico = (
        preparar_contratos_prioritarios(df_contratos)
    )

    contratos_criticos = int(
        resumo_contratos_diagnostico.get("criticos", 0)
    )
    imoveis_criticos = (
        int(
            (
                risco_imoveis_diagnostico["Classificação"]
                == "CRÍTICO"
            ).sum()
        )
        if not risco_imoveis_diagnostico.empty
        else 0
    )

    if not ranking_diagnostico.empty:
        prioridade_1 = ranking_diagnostico.iloc[0]
        prioridade_texto = (
            f"{prioridade_1['Tipo']} "
            f"{prioridade_1['Identificação']}: "
            f"{prioridade_1['Ação recomendada']}"
        )
    else:
        prioridade_texto = (
            "Revisar os itens críticos identificados no painel."
        )

    recomendacao_gerencial = (
        "Executar primeiro as ações com prazo imediato e acompanhar "
        "semanalmente a redução da inadimplência, da vacância e dos "
        "contratos em risco."
    )

    html_diagnostico = f"""<div style="
    margin-top:14px;
    border:1px solid #FCA5A5;
    border-left:6px solid #DC2626;
    border-radius:14px;
    background:rgba(239,68,68,.06);
    padding:16px 18px;
">
    <div style="
        font-weight:900;
        font-size:16px;
        margin-bottom:10px;
    ">
        Diagnóstico executivo
    </div>

    <div style="
        display:grid;
        grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
        gap:12px;
    ">
        <div>
            <div style="
                font-size:11px;
                font-weight:800;
                text-transform:uppercase;
                opacity:.68;
            ">
                Situação do mês
            </div>
            <div style="margin-top:4px;line-height:1.45;">
                Carteira em nível <strong>{classificacao_limpa}</strong>,
                com foco principal em <strong>{principal_problema}</strong>.
            </div>
        </div>

        <div>
            <div style="
                font-size:11px;
                font-weight:800;
                text-transform:uppercase;
                opacity:.68;
            ">
                Impacto financeiro
            </div>
            <div style="margin-top:4px;line-height:1.45;">
                <strong>{_moeda_br_contrato(inadimplencia)}</strong>
                de saldo inadimplente e
                <strong>{_moeda_br_contrato(abs(float(receita_perdida)))}</strong>
                de perda mensal estimada por vacância.
            </div>
        </div>

        <div>
            <div style="
                font-size:11px;
                font-weight:800;
                text-transform:uppercase;
                opacity:.68;
            ">
                Pontos críticos
            </div>
            <div style="margin-top:4px;line-height:1.45;">
                <strong>{contratos_criticos}</strong> contratos críticos e
                <strong>{imoveis_criticos}</strong> imóveis críticos
                exigem acompanhamento.
            </div>
        </div>

        <div>
            <div style="
                font-size:11px;
                font-weight:800;
                text-transform:uppercase;
                opacity:.68;
            ">
                Primeira prioridade
            </div>
            <div style="margin-top:4px;line-height:1.45;">
                {prioridade_texto}
            </div>
        </div>
    </div>

    <div style="
        margin-top:12px;
        padding-top:10px;
        border-top:1px solid rgba(220,38,38,.22);
        line-height:1.5;
    ">
        <strong>Recomendação gerencial:</strong>
        {recomendacao_gerencial}
    </div>
</div>"""

    html_diagnostico = " ".join(
        linha.strip()
        for linha in html_diagnostico.splitlines()
        if linha.strip()
    )

    st.markdown(
        html_diagnostico,
        unsafe_allow_html=True,
    )

    aba_visao, aba_pressao, aba_prioridades, aba_plano = st.tabs(
        [
            "Visão geral",
            "Riscos financeiros",
            "Prioridades",
            "Plano de ação",
        ]
    )

    with aba_visao:
        st.markdown("### Indicadores essenciais")

        linha_2 = st.columns(4)

        with linha_2[0]:
            _card_executivo_compacto(
                "Perda mensal por vacância",
                _moeda_br_contrato(abs(float(receita_perdida))),
                "Receita potencial não realizada",
                "#EA580C",
            )

        with linha_2[1]:
            _card_executivo_compacto(
                "Eficiência de ocupação",
                f"{float(eficiencia):.1f}%".replace(".", ","),
                f"{int(total_ocupados)} imóveis ocupados",
                "#2563EB",
            )

        with linha_2[2]:
            _card_executivo_compacto(
                "Ticket médio",
                _moeda_br_contrato(ticket),
                "Valor médio mensal",
                "#0891B2",
            )

        with linha_2[3]:
            _card_executivo_compacto(
                "Contratos ativos",
                str(int(ativos)),
                "Contratos atualmente monitorados",
                "#7C3AED",
            )

        st.markdown("### Leitura visual")

        col_grafico_1, col_grafico_2 = st.columns(2)

        with col_grafico_1:
            figura_receita = _figura_receita_bairros_compacta(
                receita_bairro
            )
            if figura_receita is not None:
                st.plotly_chart(
                    figura_receita,
                    use_container_width=True,
                )
            else:
                st.info(
                    "Não foi possível montar o gráfico de receita por bairro."
                )

        with col_grafico_2:
            st.plotly_chart(
                _figura_ocupacao_compacta(
                    total_ocupados,
                    total_vagos,
                ),
                use_container_width=True,
            )

    with aba_pressao:
        exibir_receita_em_risco(
            df_imoveis=df_imoveis,
            df_contratos=df_contratos,
            inadimplencia=inadimplencia,
            receita_perdida=receita_perdida,
        )

    with aba_prioridades:
        exibir_ranking_prioridades(
            df_imoveis=df_imoveis,
            df_contratos=df_contratos,
        )

    with aba_plano:
        exibir_plano_acao_mensal(
            df_imoveis=df_imoveis,
            df_contratos=df_contratos,
        )


# ==================================================
# PROCESSAMENTO
# ==================================================

if arquivo:

    planilhas = carregar_abas_imobiliaria(
        arquivo
    )

    # Mensagem técnica ocultada para manter a tela mais limpa.

    df_imoveis = obter_imoveis(planilhas)

    df_contratos = obter_contratos(planilhas)

    df_receitas = obter_receitas(planilhas)

    df_inadimplencia = obter_inadimplencia(
        planilhas
    )

    df_imoveis = normalizar_colunas(
        df_imoveis
    )

    # Filtros globais retirados da barra lateral.
    # Eles serão colocados dentro das páginas em que forem necessários.

    faltando = validar_imoveis(
        df_imoveis
    )

    if len(faltando) > 0:

        st.error(
            f"Colunas obrigatórias não encontradas: {faltando}"
        )

    else:


        # ==========================================
        # INDICADORES IMÓVEIS
        # ==========================================

        total_imoveis = len(df_imoveis)

        total_ocupados_original = imoveis_ocupados(
            df_imoveis
        )

        total_vagos = imoveis_vagos(
            df_imoveis
        )

        # Correção de consistência:
        # algumas bases informam corretamente os vagos, mas o texto de status
        # não é reconhecido pelo motor antigo. Nesses casos, ocupados é
        # calculado por total - vagos.
        total_ocupados_calculado = max(
            int(total_imoveis) - int(total_vagos),
            0,
        )

        total_ocupados = int(total_ocupados_original)

        if (
            total_ocupados < 0
            or total_ocupados > total_imoveis
            or total_ocupados + total_vagos != total_imoveis
        ):
            total_ocupados = total_ocupados_calculado

        vacancia = (
            (total_vagos / total_imoveis) * 100
            if total_imoveis
            else 0
        )

        ticket = ticket_medio(
            df_imoveis
        )

        receita_bairro = receita_por_bairro(
            df_imoveis
        )

        ranking = ranking_corretores(
            df_imoveis
        )

        # ==========================================
        # FINANCEIRO
        # ==========================================

        receita = receita_total(
            df_contratos
        )

        inadimplencia = inadimplencia_total(
            df_inadimplencia
        )

        receita_perdida = receita_perdida_vacancia(
             df_imoveis
        )
        perc_inadimplencia = percentual_inadimplencia(
            receita,
            inadimplencia
        )

        # Eficiência operacional deve refletir a ocupação real da carteira.
        eficiencia = (
            (total_ocupados / total_imoveis) * 100
            if total_imoveis
            else 0
        )
        
        ativos = contratos_ativos(
            df_contratos
        )

        vencendo = contratos_vencendo(
            df_contratos
        )

        # ==========================================
        # SCORE EXECUTIVO
        # ==========================================

        score = calcular_score(
        vacancia,
        inadimplencia,
        receita,
        vencendo
        )

        classificacao = classificar_score(
        score
        )

        resumo_score = gerar_resumo_executivo(
        score,
        classificacao
        )

        # ==========================================
        # CONTRATOS
        # ==========================================

        total_ctr = total_contratos(
            df_contratos
        )

        valor_medio_ctr = valor_medio_contrato(
            df_contratos
        )

        status_ctr = contratos_por_status(
            df_contratos
        )

        top_ctr = top_contratos_valor(
            df_contratos
        )

        vencendo_df = contratos_vencendo_df(
            df_contratos
        )

        alertas_ctr = gerar_alertas_contratos(
            df_contratos
        )

        # ==========================================
        # IA
        # ==========================================

        insights = gerar_insights_imobiliarios(
            df_imoveis
        )

        diagnostico = gerar_diagnostico_imobiliario(
            df_imoveis
        )
        # ==========================================
        # NAVEGAÇÃO
        # ==========================================

        if pagina == "📊 Executivo":

            exibir_executivo_premium_compacto(
                receita=receita,
                inadimplencia=inadimplencia,
                vacancia=vacancia,
                ticket=ticket,
                ativos=ativos,
                receita_perdida=receita_perdida,
                perc_inadimplencia=perc_inadimplencia,
                eficiencia=eficiencia,
                score=score,
                classificacao=classificacao,
                receita_bairro=receita_bairro,
                total_ocupados=total_ocupados,
                total_vagos=total_vagos,
                total_imoveis=total_imoveis,
                df_imoveis=df_imoveis,
                df_contratos=df_contratos,
            )

        elif pagina == "📈 Comparativo":

            st.subheader("Comparativo mensal")
            st.caption(
                "Compare o mês atual com o anterior e acompanhe a evolução "
                "financeira, operacional e de risco da carteira."
            )

            st.markdown(
                """
                <div style="
                    border:1px solid #334155;
                    border-radius:14px;
                    padding:14px 16px;
                    margin:6px 0 16px 0;
                    background:rgba(37,99,235,.08);
                ">
                    <strong>Objetivo da análise</strong><br>
                    Identificar rapidamente melhora, estabilidade ou piora
                    nos principais indicadores da operação imobiliária.
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.info(
                "O histórico comparativo é publicado pelo administrador "
                "e carregado automaticamente nesta tela."
            )

            _pasta_historico_cliente = _PathCliente(
                "dados_cliente/Historico"
            )

            _arquivos_historicos = sorted(
                [
                    caminho
                    for caminho in _pasta_historico_cliente.glob("*.xlsx")
                    if not caminho.name.startswith("~$")
                ],
                key=lambda caminho: caminho.stat().st_mtime,
                reverse=True,
            )

            arquivo_anterior = None

            if _arquivos_historicos:
                _caminho_historico = _arquivos_historicos[0]
                arquivo_anterior = _BytesIOCliente(
                    _caminho_historico.read_bytes()
                )
                arquivo_anterior.name = _caminho_historico.name

            if not arquivo_anterior:
                st.caption(
                    "Comparativo histórico aguardando publicação das bases mensais."
                )
            else:
                st.success(
                    "Histórico comparativo carregado automaticamente: "
                    f"{arquivo_anterior.name}"
                )
                try:
                    planilhas_ant = carregar_abas_imobiliaria(
                        arquivo_anterior
                    )

                    df_imoveis_ant = normalizar_colunas(
                        obter_imoveis(planilhas_ant)
                    )
                    df_contratos_ant = obter_contratos(
                        planilhas_ant
                    )
                    df_inadimplencia_ant = obter_inadimplencia(
                        planilhas_ant
                    )

                    faltando_ant = validar_imoveis(
                        df_imoveis_ant
                    )

                    if len(faltando_ant) > 0:
                        st.error(
                            "O arquivo anterior não possui as colunas "
                            f"obrigatórias: {faltando_ant}"
                        )
                    else:
                        total_imoveis_ant = len(df_imoveis_ant)
                        total_ocupados_ant_original = imoveis_ocupados(
                            df_imoveis_ant
                        )
                        total_vagos_ant = imoveis_vagos(
                            df_imoveis_ant
                        )

                        total_ocupados_ant_calculado = max(
                            int(total_imoveis_ant) - int(total_vagos_ant),
                            0,
                        )

                        total_ocupados_ant = int(
                            total_ocupados_ant_original
                        )

                        if (
                            total_ocupados_ant < 0
                            or total_ocupados_ant > total_imoveis_ant
                            or (
                                total_ocupados_ant + total_vagos_ant
                                != total_imoveis_ant
                            )
                        ):
                            total_ocupados_ant = (
                                total_ocupados_ant_calculado
                            )

                        vacancia_ant = (
                            (total_vagos_ant / total_imoveis_ant) * 100
                            if total_imoveis_ant
                            else 0
                        )
                        ticket_ant = ticket_medio(
                            df_imoveis_ant
                        )
                        receita_ant = receita_total(
                            df_contratos_ant
                        )
                        inadimplencia_ant = inadimplencia_total(
                            df_inadimplencia_ant
                        )
                        perc_inadimplencia_ant = percentual_inadimplencia(
                            receita_ant,
                            inadimplencia_ant,
                        )
                        ativos_ant = contratos_ativos(
                            df_contratos_ant
                        )
                        vencendo_ant = contratos_vencendo(
                            df_contratos_ant
                        )
                        score_ant = calcular_score(
                            vacancia_ant,
                            inadimplencia_ant,
                            receita_ant,
                            vencendo_ant,
                        )

                        nome_atual = getattr(
                            arquivo,
                            "name",
                            "Mês atual",
                        )
                        nome_anterior = getattr(
                            arquivo_anterior,
                            "name",
                            "Mês anterior",
                        )

                        st.success(
                            "Comparação preparada com sucesso."
                        )

                        col_arquivo_atual, col_arquivo_anterior = st.columns(2)

                        with col_arquivo_atual:
                            st.markdown("**Arquivo atual**")
                            st.markdown(
                                f"""
                                <div style="
                                    background:{"#111827" if tema_visual == "Escuro" else "#F8FAFC"};
                                    border:1px solid {sidebar_border_final};
                                    border-radius:10px;
                                    padding:12px 14px;
                                    color:{sidebar_text_final};
                                    font-family:monospace;
                                    font-size:13px;
                                ">
                                    {nome_atual}
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                        with col_arquivo_anterior:
                            st.markdown("**Arquivo anterior**")
                            st.markdown(
                                f"""
                                <div style="
                                    background:{"#111827" if tema_visual == "Escuro" else "#F8FAFC"};
                                    border:1px solid {sidebar_border_final};
                                    border-radius:10px;
                                    padding:12px 14px;
                                    color:{sidebar_text_final};
                                    font-family:monospace;
                                    font-size:13px;
                                ">
                                    {nome_anterior}
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                        def _delta_percentual(atual, anterior):
                            try:
                                if anterior == 0:
                                    return None
                                return (
                                    (atual - anterior)
                                    / abs(anterior)
                                ) * 100
                            except Exception:
                                return None

                        def _texto_delta(atual, anterior, sufixo=""):
                            delta = _delta_percentual(
                                atual,
                                anterior,
                            )
                            if delta is None:
                                return None
                            return f"{delta:+.1f}%{sufixo}"

                        st.markdown("### Painel comparativo")

                        def _moeda(valor):
                            return (
                                f"R$ {valor:,.2f}"
                                .replace(",", "X")
                                .replace(".", ",")
                                .replace("X", ".")
                            )

                        def _numero(valor):
                            return f"{int(valor)}"

                        def _percentual(valor):
                            return f"{valor:.1f}%".replace(".", ",")

                        def _variacao_percentual(atual, anterior):
                            variacao = _delta_percentual(atual, anterior)
                            if variacao is None:
                                return None
                            return variacao

                        def _variacao_pontos_num(atual, anterior):
                            return atual - anterior

                        def _variacao_inteira_num(atual, anterior):
                            return int(atual - anterior)

                        def _cor_variacao(valor, positivo_eh_bom=True):
                            if valor is None or abs(valor) < 0.05:
                                return "#94A3B8", "Estável", "→"
                            melhorou = valor > 0 if positivo_eh_bom else valor < 0
                            if melhorou:
                                return "#22C55E", "Melhora", "↑"
                            return "#EF4444", "Atenção", "↓"

                        def _card_comparativo(
                            titulo,
                            atual,
                            anterior,
                            variacao_texto,
                            variacao_num,
                            positivo_eh_bom=True,
                            icone="●",
                        ):
                            cor, status, seta = _cor_variacao(
                                variacao_num,
                                positivo_eh_bom,
                            )
                            html_card = f"""
                            <div class="td-comparativo-card" style="background:linear-gradient(145deg,rgba(255,255,255,.06),rgba(255,255,255,.02));border:1px solid rgba(148,163,184,.28);border-radius:18px;padding:18px 18px 16px 18px;min-height:182px;box-shadow:0 10px 26px rgba(15,23,42,.12);backdrop-filter:blur(6px);">
                                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
                                    <div style="font-size:14px;font-weight:800;letter-spacing:.2px;">{icone} {titulo}</div>
                                    <div style="color:{cor};background:{cor}20;border:1px solid {cor}55;border-radius:999px;padding:4px 9px;font-size:11px;font-weight:800;">{seta} {status}</div>
                                </div>
                                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                                    <div style="background:rgba(148,163,184,.08);border-radius:12px;padding:11px 12px;">
                                        <div style="font-size:10px;text-transform:uppercase;letter-spacing:.8px;opacity:.72;margin-bottom:4px;">Mês anterior</div>
                                        <div style="font-size:18px;font-weight:800;">{anterior}</div>
                                    </div>
                                    <div style="background:rgba(37,99,235,.10);border:1px solid rgba(59,130,246,.22);border-radius:12px;padding:11px 12px;">
                                        <div style="font-size:10px;text-transform:uppercase;letter-spacing:.8px;opacity:.72;margin-bottom:4px;">Mês atual</div>
                                        <div style="font-size:18px;font-weight:900;">{atual}</div>
                                    </div>
                                </div>
                                <div style="margin-top:12px;display:flex;justify-content:space-between;align-items:center;">
                                    <span style="font-size:11px;opacity:.72;">Variação no período</span>
                                    <strong style="color:{cor};font-size:15px;">{variacao_texto}</strong>
                                </div>
                            </div>
                            """
                            return "".join(
                                linha.strip()
                                for linha in html_card.splitlines()
                            )

                        indicadores_cards = [
                            (
                                "Receita",
                                _moeda(receita),
                                _moeda(receita_ant),
                                (
                                    "—"
                                    if _variacao_percentual(receita, receita_ant) is None
                                    else f"{_variacao_percentual(receita, receita_ant):+.1f}%".replace(".", ",")
                                ),
                                _variacao_percentual(receita, receita_ant),
                                True,
                                "💰",
                            ),
                            (
                                "Inadimplência",
                                _moeda(inadimplencia),
                                _moeda(inadimplencia_ant),
                                (
                                    "—"
                                    if _variacao_percentual(inadimplencia, inadimplencia_ant) is None
                                    else f"{_variacao_percentual(inadimplencia, inadimplencia_ant):+.1f}%".replace(".", ",")
                                ),
                                _variacao_percentual(inadimplencia, inadimplencia_ant),
                                False,
                                "⚠️",
                            ),
                            (
                                "Vacância",
                                _percentual(vacancia),
                                _percentual(vacancia_ant),
                                f"{_variacao_pontos_num(vacancia, vacancia_ant):+.1f} p.p.".replace(".", ","),
                                _variacao_pontos_num(vacancia, vacancia_ant),
                                False,
                                "🏢",
                            ),
                            (
                                "Score",
                                _numero(score),
                                _numero(score_ant),
                                f"{_variacao_inteira_num(score, score_ant):+d} pontos",
                                _variacao_inteira_num(score, score_ant),
                                True,
                                "🎯",
                            ),
                            (
                                "Imóveis ocupados",
                                _numero(total_ocupados),
                                _numero(total_ocupados_ant),
                                f"{_variacao_inteira_num(total_ocupados, total_ocupados_ant):+d}",
                                _variacao_inteira_num(total_ocupados, total_ocupados_ant),
                                True,
                                "✅",
                            ),
                            (
                                "Imóveis vagos",
                                _numero(total_vagos),
                                _numero(total_vagos_ant),
                                f"{_variacao_inteira_num(total_vagos, total_vagos_ant):+d}",
                                _variacao_inteira_num(total_vagos, total_vagos_ant),
                                False,
                                "🚪",
                            ),
                            (
                                "Contratos ativos",
                                _numero(ativos),
                                _numero(ativos_ant),
                                f"{_variacao_inteira_num(ativos, ativos_ant):+d}",
                                _variacao_inteira_num(ativos, ativos_ant),
                                True,
                                "📄",
                            ),
                            (
                                "Ticket médio",
                                _moeda(ticket),
                                _moeda(ticket_ant),
                                (
                                    "—"
                                    if _variacao_percentual(ticket, ticket_ant) is None
                                    else f"{_variacao_percentual(ticket, ticket_ant):+.1f}%".replace(".", ",")
                                ),
                                _variacao_percentual(ticket, ticket_ant),
                                True,
                                "📈",
                            ),
                        ]

                        for inicio in range(0, len(indicadores_cards), 4):
                            colunas_cards = st.columns(4)
                            for coluna, dados in zip(
                                colunas_cards,
                                indicadores_cards[inicio:inicio + 4],
                            ):
                                with coluna:
                                    st.markdown(
                                        _card_comparativo(*dados),
                                        unsafe_allow_html=True,
                                    )

                        st.markdown("### Resumo executivo do período")

                        variacoes_criticas = []
                        variacoes_positivas = []

                        receita_var = _variacao_percentual(receita, receita_ant)
                        inad_var = _variacao_percentual(
                            inadimplencia,
                            inadimplencia_ant,
                        )
                        vac_var = _variacao_pontos_num(vacancia, vacancia_ant)
                        score_var = _variacao_inteira_num(score, score_ant)
                        ocupados_var = _variacao_inteira_num(
                            total_ocupados,
                            total_ocupados_ant,
                        )
                        vagos_var = _variacao_inteira_num(
                            total_vagos,
                            total_vagos_ant,
                        )
                        contratos_var = _variacao_inteira_num(
                            ativos,
                            ativos_ant,
                        )
                        ticket_var = _variacao_percentual(
                            ticket,
                            ticket_ant,
                        )

                        if receita_var is not None:
                            if receita_var > 0.05:
                                variacoes_positivas.append(
                                    f"Receita cresceu {receita_var:.1f}%."
                                )
                            elif receita_var < -0.05:
                                variacoes_criticas.append(
                                    f"Receita caiu {abs(receita_var):.1f}%."
                                )

                        if inad_var is not None:
                            if inad_var < -0.05:
                                variacoes_positivas.append(
                                    f"Inadimplência caiu {abs(inad_var):.1f}%."
                                )
                            elif inad_var > 0.05:
                                variacoes_criticas.append(
                                    f"Inadimplência subiu {inad_var:.1f}%."
                                )

                        if vac_var < -0.05:
                            variacoes_positivas.append(
                                f"Vacância reduziu {abs(vac_var):.1f} p.p."
                            )
                        elif vac_var > 0.05:
                            variacoes_criticas.append(
                                f"Vacância aumentou {vac_var:.1f} p.p."
                            )

                        if score_var > 0:
                            variacoes_positivas.append(
                                f"Score avançou {score_var} pontos."
                            )
                        elif score_var < 0:
                            variacoes_criticas.append(
                                f"Score recuou {abs(score_var)} pontos."
                            )

                        if ocupados_var > 0:
                            variacoes_positivas.append(
                                f"Imóveis ocupados aumentaram em {ocupados_var}."
                            )
                        elif ocupados_var < 0:
                            variacoes_criticas.append(
                                f"Imóveis ocupados reduziram em {abs(ocupados_var)}."
                            )

                        if vagos_var < 0:
                            variacoes_positivas.append(
                                f"Imóveis vagos reduziram em {abs(vagos_var)}."
                            )
                        elif vagos_var > 0:
                            variacoes_criticas.append(
                                f"Imóveis vagos aumentaram em {vagos_var}."
                            )

                        if contratos_var > 0:
                            variacoes_positivas.append(
                                f"Contratos ativos aumentaram em {contratos_var}."
                            )
                        elif contratos_var < 0:
                            variacoes_criticas.append(
                                f"Contratos ativos reduziram em {abs(contratos_var)}."
                            )

                        if ticket_var is not None:
                            if ticket_var > 0.05:
                                variacoes_positivas.append(
                                    f"Ticket médio cresceu {ticket_var:.1f}%."
                                )
                            elif ticket_var < -0.05:
                                variacoes_criticas.append(
                                    f"Ticket médio caiu {abs(ticket_var):.1f}%."
                                )

                        col_resumo_positivo, col_resumo_atencao = st.columns(2)

                        with col_resumo_positivo:
                            st.markdown(
                                textwrap.dedent("""
                                <div style="
                                    border-left:5px solid #22C55E;
                                    background:rgba(34,197,94,.10);
                                    border-radius:14px;
                                    padding:16px 18px;
                                    min-height:130px;
                                ">
                                    <div style="
                                        font-weight:900;
                                        margin-bottom:8px;
                                    ">Pontos positivos</div>
                                    <div style="line-height:1.7;">
                                """
                                + (
                                    "<br>".join(
                                        f"• {item}"
                                        for item in variacoes_positivas
                                    )
                                    if variacoes_positivas
                                    else "• Não houve melhora relevante no período."
                                )
                                + """
                                    </div>
                                </div>
                                """).strip(),
                                unsafe_allow_html=True,
                            )

                        with col_resumo_atencao:
                            st.markdown(
                                textwrap.dedent("""
                                <div style="
                                    border-left:5px solid #EF4444;
                                    background:rgba(239,68,68,.10);
                                    border-radius:14px;
                                    padding:16px 18px;
                                    min-height:130px;
                                ">
                                    <div style="
                                        font-weight:900;
                                        margin-bottom:8px;
                                    ">Pontos de atenção</div>
                                    <div style="line-height:1.7;">
                                """
                                + (
                                    "<br>".join(
                                        f"• {item}"
                                        for item in variacoes_criticas
                                    )
                                    if variacoes_criticas
                                    else "• Nenhum alerta relevante identificado."
                                )
                                + """
                                    </div>
                                </div>
                                """).strip(),
                                unsafe_allow_html=True,
                            )

                        ocupacao_atual = (
                            (total_ocupados / total_imoveis) * 100
                            if total_imoveis
                            else 0
                        )
                        ocupacao_anterior = (
                            (
                                total_ocupados_ant
                                / total_imoveis_ant
                            ) * 100
                            if total_imoveis_ant
                            else 0
                        )

                        col_financeiro, col_operacional = st.columns(2)

                        with col_financeiro:
                            figura_financeira = go.Figure()
                            figura_financeira.add_trace(
                                go.Bar(
                                    name="Mês anterior",
                                    x=["Receita", "Inadimplência"],
                                    y=[receita_ant, inadimplencia_ant],
                                    text=[
                                        f"R$ {receita_ant:,.0f}",
                                        f"R$ {inadimplencia_ant:,.0f}",
                                    ],
                                    textposition="outside",
                                )
                            )
                            figura_financeira.add_trace(
                                go.Bar(
                                    name="Mês atual",
                                    x=["Receita", "Inadimplência"],
                                    y=[receita, inadimplencia],
                                    text=[
                                        f"R$ {receita:,.0f}",
                                        f"R$ {inadimplencia:,.0f}",
                                    ],
                                    textposition="outside",
                                )
                            )
                            figura_financeira.update_layout(
                                title="Evolução financeira",
                                barmode="group",
                                height=390,
                                yaxis_title="Valor (R$)",
                            )
                            st.plotly_chart(
                                figura_financeira,
                                use_container_width=True,
                            )

                        with col_operacional:
                            figura_operacional = go.Figure()
                            figura_operacional.add_trace(
                                go.Bar(
                                    name="Mês anterior",
                                    x=[
                                        "Vacância",
                                        "Ocupação",
                                        "Score",
                                    ],
                                    y=[
                                        vacancia_ant,
                                        ocupacao_anterior,
                                        score_ant,
                                    ],
                                    text=[
                                        f"{vacancia_ant:.1f}%",
                                        f"{ocupacao_anterior:.1f}%",
                                        f"{score_ant:.0f}",
                                    ],
                                    textposition="outside",
                                )
                            )
                            figura_operacional.add_trace(
                                go.Bar(
                                    name="Mês atual",
                                    x=[
                                        "Vacância",
                                        "Ocupação",
                                        "Score",
                                    ],
                                    y=[
                                        vacancia,
                                        ocupacao_atual,
                                        score,
                                    ],
                                    text=[
                                        f"{vacancia:.1f}%",
                                        f"{ocupacao_atual:.1f}%",
                                        f"{score:.0f}",
                                    ],
                                    textposition="outside",
                                )
                            )
                            figura_operacional.update_layout(
                                title="Evolução operacional",
                                barmode="group",
                                height=390,
                                yaxis_title="Índice",
                                yaxis=dict(range=[0, 110]),
                            )
                            st.plotly_chart(
                                figura_operacional,
                                use_container_width=True,
                            )

                        st.markdown("### Relatório comparativo")

                        periodo_atual_pdf = identificar_periodo_arquivo_imobiliaria(
                            nome_atual
                        )
                        periodo_anterior_pdf = identificar_periodo_arquivo_imobiliaria(
                            nome_anterior
                        )

                        nome_imobiliaria_comparativo = st.text_input(
                            "Nome da imobiliária para o relatório comparativo",
                            value="Imobiliária demonstrativa",
                            key="nome_imobiliaria_comparativo_v44",
                        )

                        if st.button(
                            "Gerar relatório comparativo em PDF",
                            type="primary",
                            use_container_width=True,
                            key="gerar_pdf_comparativo_v44",
                        ):
                            pdf_comparativo = gerar_pdf_comparativo_imobiliaria(
                                nome_imobiliaria=nome_imobiliaria_comparativo,
                                periodo_atual=periodo_atual_pdf,
                                periodo_anterior=periodo_anterior_pdf,
                                nome_arquivo_atual=nome_atual,
                                nome_arquivo_anterior=nome_anterior,
                                receita_atual=receita,
                                receita_anterior=receita_ant,
                                inadimplencia_atual=inadimplencia,
                                inadimplencia_anterior=inadimplencia_ant,
                                vacancia_atual=vacancia,
                                vacancia_anterior=vacancia_ant,
                                score_atual=score,
                                score_anterior=score_ant,
                                ocupados_atual=total_ocupados,
                                ocupados_anterior=total_ocupados_ant,
                                vagos_atual=total_vagos,
                                vagos_anterior=total_vagos_ant,
                                contratos_ativos_atual=ativos,
                                contratos_ativos_anterior=ativos_ant,
                                ticket_atual=ticket,
                                ticket_anterior=ticket_ant,
                            )

                            st.session_state[
                                "pdf_comparativo_imobiliaria_v44"
                            ] = pdf_comparativo

                            st.success(
                                "Relatório comparativo gerado com sucesso."
                            )

                        pdf_comparativo_disponivel = st.session_state.get(
                            "pdf_comparativo_imobiliaria_v44"
                        )

                        if pdf_comparativo_disponivel:
                            nome_download_comparativo = (
                                "Relatorio_Comparativo_"
                                + str(nome_imobiliaria_comparativo)
                                .strip()
                                .replace(" ", "_")
                                + "_"
                                + str(periodo_anterior_pdf)
                                .replace("/", "-")
                                + "_x_"
                                + str(periodo_atual_pdf)
                                .replace("/", "-")
                                + ".pdf"
                            )

                            st.download_button(
                                "Baixar relatório comparativo em PDF",
                                data=pdf_comparativo_disponivel,
                                file_name=nome_download_comparativo,
                                mime="application/pdf",
                                use_container_width=True,
                                key="download_pdf_comparativo_v44",
                            )


                except Exception as erro_comparativo:
                    st.error(
                        "Não foi possível processar o arquivo anterior. "
                        f"Detalhe: {erro_comparativo}"
                    )

        elif pagina == "🏢 Gestão Carteira":

            aba_imoveis, aba_contratos, aba_riscos = st.tabs(
                ["Imóveis", "Contratos", "Riscos"]
            )

            with aba_imoveis:
                exibir_imoveis(
                    total_imoveis,
                    total_ocupados,
                    total_vagos,
                    vacancia,
                    ticket,
                    receita_bairro,
                    ranking,
                    card_imoveis_totais,
                    card_imoveis_ocupados,
                    card_imoveis_vagos,
                    card_vacancia,
                    card_ticket_medio,
                    grafico_receita_bairro,
                    grafico_ranking_corretores,
                    grafico_status_imoveis,
                    df_imoveis
                )

                exibir_indice_risco_imoveis(
                    df_imoveis
                )

            with aba_contratos:
                exibir_contratos(
                    total_ctr,
                    ativos,
                    valor_medio_ctr,
                    vencendo_df,
                    status_ctr,
                    top_ctr,
                    alertas_ctr,
                    card_total_contratos,
                    card_contratos_ativos,
                    card_contratos_vencendo,
                    card_valor_medio_contrato,
                    grafico_contratos_status,
                    grafico_top_contratos,
                    grafico_contratos_vencendo
                )

                st.divider()
                exibir_contratos_prioritarios(
                    df_contratos
                )

            with aba_riscos:
                exibir_riscos(
                    df_inadimplencia,
                    grafico_top_inadimplentes,
                    grafico_inadimplencia_bairro
                )

        elif pagina == "📄 Relatório":

            st.subheader("Relatório executivo")
            st.caption(
                "Gere o PDF do período atual com os principais indicadores, "
                "diagnóstico e recomendações."
            )

            nome_arquivo_relatorio = getattr(
                arquivo,
                "name",
                "Arquivo imobiliário",
            )

            periodo_automatico = identificar_periodo_arquivo_imobiliaria(
                nome_arquivo_relatorio
            )

            col_nome_relatorio, col_periodo_relatorio = st.columns(2)

            with col_nome_relatorio:
                nome_imobiliaria_relatorio = st.text_input(
                    "Nome da imobiliária",
                    value="Imobiliária demonstrativa",
                    key="nome_imobiliaria_relatorio_v29",
                )

            with col_periodo_relatorio:
                periodo_relatorio = st.text_input(
                    "Período analisado",
                    value=periodo_automatico,
                    key="periodo_imobiliaria_relatorio_v29",
                    help=(
                        "O período é preenchido automaticamente pelo nome "
                        "do arquivo. Quando o arquivo não informa o mês, "
                        "o sistema usa o mês atual."
                    ),
                )

            st.markdown("### Prévia do relatório")

            previa_1 = st.columns(4)
            previa_1[0].metric(
                "Receita",
                _moeda_br_contrato(receita),
            )
            previa_1[1].metric(
                "Inadimplência",
                _moeda_br_contrato(inadimplencia),
            )
            previa_1[2].metric(
                "Vacância",
                f"{float(vacancia):.1f}%".replace(".", ","),
            )
            previa_1[3].metric(
                "Score",
                f"{float(score):.0f}/100",
                help=(
                    "0 a 49 = Crítico | "
                    "50 a 79 = Atenção | "
                    "80 a 100 = Saudável"
                ),
            )

            st.caption(
                "Leitura do score: 0 a 49 = Crítico | "
                "50 a 79 = Atenção | 80 a 100 = Saudável."
            )

            previa_2 = st.columns(4)
            previa_2[0].metric("Imóveis", total_imoveis)
            previa_2[1].metric("Ocupados", total_ocupados)
            previa_2[2].metric("Vagos", total_vagos)
            previa_2[3].metric("Contratos ativos", ativos)

            pode_gerar_relatorio = bool(
                str(nome_imobiliaria_relatorio).strip()
                and str(periodo_relatorio).strip()
            )

            if not pode_gerar_relatorio:
                st.info(
                    "Preencha o nome da imobiliária e o período analisado "
                    "para liberar a geração do PDF."
                )

            if st.button(
                "Gerar relatório executivo",
                type="primary",
                use_container_width=True,
                disabled=not pode_gerar_relatorio,
                key="gerar_relatorio_imobiliaria_v29",
            ):
                pdf_relatorio = gerar_pdf_imobiliaria_mes_atual(
                    nome_imobiliaria=nome_imobiliaria_relatorio,
                    periodo=periodo_relatorio,
                    nome_arquivo=nome_arquivo_relatorio,
                    receita=receita,
                    inadimplencia=inadimplencia,
                    vacancia=vacancia,
                    ticket=ticket,
                    total_imoveis=total_imoveis,
                    total_ocupados=total_ocupados,
                    total_vagos=total_vagos,
                    contratos_ativos_qtd=ativos,
                    contratos_vencendo_qtd=vencendo,
                    receita_perdida=receita_perdida,
                    percentual_inadimplencia_valor=perc_inadimplencia,
                    eficiencia=eficiencia,
                    score=score,
                    classificacao=classificacao,
                    resumo_score=resumo_score,
                    diagnostico=diagnostico,
                    insights=insights,
                    df_imoveis=df_imoveis,
                    df_contratos=df_contratos,
                )

                st.session_state[
                    "pdf_imobiliaria_mes_atual_v29"
                ] = pdf_relatorio

                st.success(
                    "Relatório executivo gerado com sucesso."
                )

            pdf_disponivel = st.session_state.get(
                "pdf_imobiliaria_mes_atual_v29"
            )

            if pdf_disponivel:
                nome_download = (
                    "Relatorio_Executivo_"
                    + str(nome_imobiliaria_relatorio)
                    .strip()
                    .replace(" ", "_")
                    + "_"
                    + str(periodo_relatorio)
                    .strip()
                    .replace("/", "-")
                    .replace(" ", "_")
                    + ".pdf"
                )

                st.download_button(
                    "Baixar relatório executivo em PDF",
                    data=pdf_disponivel,
                    file_name=nome_download,
                    mime="application/pdf",
                    use_container_width=True,
                    key="download_relatorio_imobiliaria_v29",
                )

        elif pagina == "🤖 Insights":

            exibir_insights(
                df_imoveis,
                gerar_insights_imobiliarios,
                gerar_diagnostico_imobiliario
            )

        elif pagina == "⚙️ Dados":

            exibir_dados(
                df_imoveis,
                df_contratos,
                df_receitas,
                df_inadimplencia
            )