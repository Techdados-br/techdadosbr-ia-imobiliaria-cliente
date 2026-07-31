from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Image,
    Table,
    TableStyle
)

from reportlab.lib import colors

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

from reportlab.lib.enums import TA_CENTER

from datetime import datetime

from graficos_pdf.gerador_graficos import (
    salvar_grafico_receita_bairro,
    salvar_grafico_inadimplencia,
    salvar_grafico_vacancia
)

def moeda_br(valor):

    try:

        return (
            f"R$ {valor:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    except:

        return "R$ 0,00"
    
def percentual_br(valor, casas=1):

    try:

        return (
            f"{valor:.{casas}f}%"
            .replace(".", ",")
        )

    except:

        return "0,0%"


def limpar_classificacao(valor):

    try:

        texto = str(valor).upper()

        if "CRÍTICA" in texto or "CRITICA" in texto:
            return "CRÍTICA"

        if "ATENÇÃO" in texto or "ATENCAO" in texto:
            return "ATENÇÃO"

        if "SAUDÁVEL" in texto or "SAUDAVEL" in texto:
            return "SAUDÁVEL"

        return texto.replace("■", "").strip()

    except:

        return ""

    
def gerar_pdf_imobiliaria(
        caminho_pdf,
        imoveis_totais,
        imoveis_ocupados,
        imoveis_vagos,
        vacancia,
        ticket_medio,
        receita,
        inadimplencia,
        contratos_ativos,
        contratos_vencendo,
        diagnostico,
        insights,
        receita_bairro,
        df_inadimplencia,
        score,
        classificacao,
        receita_perdida,
        perc_inadimplencia,
        eficiencia,
        
    ):
    doc = SimpleDocTemplate(
        caminho_pdf
    )

    styles = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "Titulo",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0F6FFF")
    )

    subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#003366")
    )

    elementos = []

    data_emissao = datetime.now().strftime(
        "%d/%m/%Y %H:%M"
    )

    classificacao = limpar_classificacao(classificacao)

    # ==========================================
    # GERAÇÃO DOS GRÁFICOS
    # ==========================================

    try:

        salvar_grafico_receita_bairro(
            receita_bairro
        )

    except Exception as erro:

        print(
            f"Erro gráfico receita: {erro}"
        )

    try:

        salvar_grafico_inadimplencia(
            df_inadimplencia
        )

    except Exception as erro:

        print(
            f"Erro gráfico inadimplência: {erro}"
        )
   
    try:

        salvar_grafico_vacancia(
            imoveis_ocupados,
            imoveis_vagos
        )

    except Exception as erro:

        print(
        f"Erro gráfico vacância: {erro}"
        )

    # ==========================================
    # CAPA
    # ==========================================

    try:

        logo = Image(
            "assets/logo_techdadosbr.png",
            width=140,
            height=140
        )

        elementos.append(
            logo
        )

    except:

        pass

    elementos.append(
        Spacer(1, 35)
    )
    
    elementos.append(
        Paragraph(
            "RELATÓRIO EXECUTIVO IMOBILIÁRIO",
            subtitulo
        )
    )

    elementos.append(
       Spacer(1, 20)
    )

    capa_info = Table(
        [
            ["Data de Emissão", data_emissao],
            ["Classificação", classificacao],
            ["Score Geral", f"{score}/100"]
        ],
        colWidths=[150, 180]
    )

    capa_info.setStyle(
        TableStyle([
            ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#0F6FFF")),
            ("TEXTCOLOR",(0,0),(0,-1),colors.white),
            ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),
            ("GRID",(0,0),(-1,-1),1,colors.HexColor("#D9D9D9")),
            ("BACKGROUND",(1,0),(1,-1),colors.whitesmoke)
        ])
    )

    elementos.append(
        capa_info
    )

    elementos.append(
        Spacer(1, 15)
    )

    elementos.append(
       Paragraph(
           "Resumo Executivo",
           styles["Heading1"]
       )
    )

    elementos.append(
       Spacer(1, 20)
    )

    tabela_score = Table(
        [
             ["Indicador", "Valor"],
             ["Score Geral", str(score)],
             ["Classificação", classificacao],
             ["Receita Perdida", moeda_br(receita_perdida)],
             ["% Inadimplência", percentual_br(perc_inadimplencia, 2)],
             ["Eficiência de Ocupação", percentual_br(eficiencia, 2)]
        ],
        colWidths=[250, 200]
    )

    tabela_score.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F6FFF")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black)
         ])
    )

    elementos.append(
        tabela_score
    )

    elementos.append(
    Spacer(1, 10)
    )

    cards_executivos = Table(
    [
        [
            f"SCORE\n\n{score}/100",
            f"STATUS\n\n{classificacao}"
        ],
        [
            f"INADIMPLÊNCIA\n\n{percentual_br(perc_inadimplencia, 1)}",
            f"EFICIÊNCIA\n\n{percentual_br(eficiencia, 1)}"
        ]
    ],
    colWidths=[220, 220],
    rowHeights=[60, 60]
)

    cards_executivos.setStyle(
        TableStyle([
            ("BACKGROUND",(0,0),(0,0),colors.HexColor("#DFF5E1")),
            ("BACKGROUND",(1,0),(1,0),colors.HexColor("#FFE5E5")),
            ("BACKGROUND",(0,1),(0,1),colors.HexColor("#FFF4CC")),
            ("BACKGROUND",(1,1),(1,1),colors.HexColor("#E6F0FF")),
            ("GRID",(0,0),(-1,-1),1,colors.white),
            ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),
            ("FONTSIZE",(0,0),(-1,-1),12),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE")
        ])
    )

    elementos.append(
        cards_executivos
    )

    # ==========================================
    # DASHBOARD
    # ==========================================

    elementos.append(
        PageBreak()
    )

    elementos.append(
        Paragraph(
            "Dashboard Executivo",
            styles["Heading1"]
        )
    )

    elementos.append(
        Spacer(1, 5)
    )

    cards_dashboard = Table(
        [
            [
                f"RECEITA\n\n{moeda_br(receita)}",
                f"INADIMPLÊNCIA\n\n{moeda_br(inadimplencia)}"
            ],
            [
                f"VACÂNCIA\n\n{percentual_br(vacancia, 1)}",
                f"VENCENDO\n\n{contratos_vencendo}"
            ]
        ],
        colWidths=[220,220],
        rowHeights=[50,50]
    )

    cards_dashboard.setStyle(
        TableStyle([
            ("BACKGROUND",(0,0),(0,0),colors.HexColor("#E8F5E9")),
            ("BACKGROUND",(1,0),(1,0),colors.HexColor("#FFF4CC")),
            ("BACKGROUND",(0,1),(0,1),colors.HexColor("#E6F0FF")),
            ("BACKGROUND",(1,1),(1,1),colors.HexColor("#FFE5E5")),
            ("GRID",(0,0),(-1,-1),1,colors.white),
            ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),
            ("FONTSIZE",(0,0),(-1,-1),12),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE")
        ])     
    )

    elementos.append(
        cards_dashboard
    )

    elementos.append(
        Spacer(1, 8)
    )

    try:

        tabela_graficos = Table(
    [[
            Image(
               "assets/grafico_receita.png",
                width=210,
                height=140
            ),
            Image(
               "assets/grafico_inadimplencia.png",
                width=210,
                height=140
            )
        ]]
    )
        elementos.append(
            tabela_graficos
        )

    except:

        pass

    elementos.append(
        Spacer(1, 3)
    )

    try:

        elementos.append(
            Image(
                "assets/grafico_vacancia.png",
                width=380,
                height=80
            )           
        )

    except:

        pass

    elementos.append(
        Spacer(1, 0)
    )

    # ==========================================
    # INDICADORES IMOBILIÁRIOS
    # ==========================================

    elementos.append(
        Paragraph(
            "Indicadores Imobiliários",
            styles["Heading1"]
        )
    )

    elementos.append(
        Spacer(1, 3)
    )

    tabela_imoveis = Table(
        [
            ["Indicador", "Valor"],
            ["Imóveis Totais", str(imoveis_totais)],
            ["Imóveis Ocupados", str(imoveis_ocupados)],
            ["Imóveis Vagos", str(imoveis_vagos)],
            ["Vacância", percentual_br(vacancia, 1)],
            ["Ticket Médio", moeda_br(ticket_medio)]
        ],
        colWidths=[250, 200]
    )

    tabela_imoveis.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F6FFF")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black)
        ])
    )

    elementos.append(
        tabela_imoveis
    )

    elementos.append(
        Spacer(1, 0)
    )

    # ==========================================
    # INDICADORES FINANCEIROS
    # ==========================================

    elementos.append(
        Paragraph(
            "Indicadores Financeiros",
            styles["Heading1"]
        )
    )

    elementos.append(
        Spacer(1, 3)
    )

    tabela_financeira = Table(
        [
            ["Indicador", "Valor"],
            ["Receita Total", moeda_br(receita)],
            ["Inadimplência", moeda_br(inadimplencia)],
            ["Contratos Ativos", str(contratos_ativos)],
            ["Contratos Vencendo", str(contratos_vencendo)]
        ],
        colWidths=[200, 160]
    )

    tabela_financeira.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black)
        ])
    )

    elementos.append(
        tabela_financeira
    )

    elementos.append(
        Spacer(1, 15)
    )

    elementos.append(
    PageBreak()
    )

    # ==========================================
    # DIAGNÓSTICO
    # ==========================================

    elementos.append(
        Paragraph(
            "Diagnóstico Inteligente",
            styles["Heading1"]
        )
    )

    elementos.append(
        Spacer(1, 10)
    )

    for item in diagnostico:

        tabela_diag = Table(
           [[item]],
           colWidths=[450]
        )

        tabela_diag.setStyle(
            TableStyle([
           ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#FFF4CC")),
           ("BOX",(0,0),(-1,-1),1,colors.HexColor("#D6B656")),
           ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),
           ("FONTSIZE",(0,0),(-1,-1),11),
           ("LEFTPADDING",(0,0),(-1,-1),10),
           ("TOPPADDING",(0,0),(-1,-1),12),
           ("BOTTOMPADDING",(0,0),(-1,-1),12)
        ])
    )

        elementos.append(
            tabela_diag
        )

        elementos.append(
            Spacer(1,10)
        )

    # ==========================================
    # INSIGHTS
    # ==========================================

    elementos.append(
        Paragraph(
            "Insights Estratégicos",
            styles["Heading1"]
        )
    )

    elementos.append(
        Spacer(1, 10)
    )

    for insight in insights:

        insight = str(insight).replace(
            f"{vacancia:.1f}%",
            percentual_br(vacancia, 1)
        )

        tabela_insight = Table(
           [[insight]],
            colWidths=[450]
        )

        tabela_insight.setStyle(
            TableStyle([
          ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#E8F5E9")),
          ("BOX",(0,0),(-1,-1),1,colors.HexColor("#2E8B57")),
          ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),
          ("FONTSIZE",(0,0),(-1,-1),11),
          ("LEFTPADDING",(0,0),(-1,-1),10),
          ("TOPPADDING",(0,0),(-1,-1),12),
          ("BOTTOMPADDING",(0,0),(-1,-1),12)
        ])
    )

        elementos.append(
            tabela_insight
        )

        elementos.append(
            Spacer(1, 5)
     )

    elementos.append(
         Spacer(1, 20)
    )

    elementos.append(
        Paragraph(
            "Parecer Executivo",
                styles["Heading1"]
        )
    )

    vacancia_parecer = percentual_br(vacancia, 1)

    parecer = f"""
    <b>STATUS GERAL:</b> {classificacao}

    <br/><br/>

    <b>Vacância Atual:</b> {vacancia_parecer}

    <br/><br/>

    <b>Inadimplência Atual:</b> {percentual_br(perc_inadimplencia, 1)}

    <br/><br/>

    <b>Eficiência Operacional:</b> {percentual_br(eficiencia, 1)}

    <br/><br/>

    <b>Potencial de Recuperação:</b>
    {moeda_br(receita_perdida)}

    <br/><br/>

    <b>Recomendação Prioritária:</b>

    Atuar imediatamente na ocupação dos imóveis vagos,
    renovação dos contratos próximos ao vencimento
    e reforço das ações de cobrança para redução da
    inadimplência.
    """

    tabela_parecer = Table(
       [[Paragraph(
           parecer,
          styles["BodyText"]
        )]],
        colWidths=[450]
    )

    tabela_parecer.setStyle(
       TableStyle([
           ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#E6F0FF")),
           ("BOX",(0,0),(-1,-1),1,colors.HexColor("#0F6FFF")),
           ("LEFTPADDING",(0,0),(-1,-1),12),
           ("TOPPADDING",(0,0),(-1,-1),12),
           ("BOTTOMPADDING",(0,0),(-1,-1),12)
        ])
    )

    elementos.append(
        tabela_parecer
    )

    # ==========================================
    # GERA PDF
    # ==========================================

    elementos.append(
        Spacer(1,5)
    )

    elementos.append(
       Paragraph(
           f"Relatório emitido em {data_emissao}",
            styles["Italic"]
        )
    )   

    doc.build(
        elementos
    )

    print("PDF GERADO COM SUCESSO")

   