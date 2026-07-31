import streamlit as st
import tempfile
import os

from relatorios.pdf_imobiliaria import gerar_pdf_imobiliaria


# ============================================================
# FORMATAÇÃO
# ============================================================

def moeda_br(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def moeda_br_negativa(valor):
    try:
        v = abs(float(valor))
        texto = f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"- {texto}"
    except Exception:
        return "- R$ 0,00"


def percentual_br(valor, casas=1):
    try:
        return f"{float(valor):.{casas}f}%".replace(".", ",")
    except Exception:
        return "0,0%"


def classificar_visual(classificacao):
    texto = str(classificacao).upper().strip()

    if "CRÍTICA" in texto or "CRITICA" in texto:
        return "critica", "CRÍTICA"

    if "ATENÇÃO" in texto or "ATENCAO" in texto:
        return "atencao", "ATENÇÃO"

    return "saudavel", "SAUDÁVEL"


# ============================================================
# TEMA / CSS
# ============================================================

def cores_tema():
    tema = st.session_state.get("tema_visual_imob", "Claro")

    if tema == "Escuro":
        return {
            "bg": "#0F172A",
            "card": "#111827",
            "card2": "#162033",
            "text": "#F8FAFC",
            "muted": "#CBD5E1",
            "border": "#334155",
            "shadow": "0 12px 28px rgba(0,0,0,.35)",
            "plot_bg": "#0F172A",
            "plot_grid": "#263244",
            "plot_font": "#F8FAFC",
        }

    return {
        "bg": "#F3F6FA",
        "card": "#FFFFFF",
        "card2": "#F8FAFC",
        "text": "#0F172A",
        "muted": "#475569",
        "border": "#CBD5E1",
        "shadow": "0 12px 28px rgba(15,23,42,.12)",
        "plot_bg": "#F3F6FA",
        "plot_grid": "#D8E0EA",
        "plot_font": "#0F172A",
    }


def aplicar_css():
    c = cores_tema()

    st.markdown(
        f"""
        <style>
            .stApp {{
                background: {c["bg"]};
                color: {c["text"]};
            }}

            section[data-testid="stSidebar"] {{
                background: {c["card2"]};
                border-right: 1px solid {c["border"]};
            }}

            .td-section {{
                margin-top: 34px;
                margin-bottom: 14px;
            }}

            .td-section h3 {{
                color: {c["text"]};
                margin-bottom: 4px;
                font-size: 24px;
                font-weight: 850;
            }}

            .td-section p {{
                color: {c["muted"]};
                margin-top: 0;
                font-size: 13px;
            }}

            .td-card {{
                background: {c["card"]};
                border: 1px solid {c["border"]};
                border-left: 6px solid var(--accent);
                border-radius: 16px;
                padding: 18px 18px;
                min-height: 116px;
                box-shadow: {c["shadow"]};
            }}

            .td-card-label {{
                color: {c["muted"]};
                font-size: 12px;
                font-weight: 850;
                text-transform: uppercase;
                letter-spacing: .04em;
                margin-bottom: 12px;
            }}

            .td-card-value {{
                color: var(--value-color, {c["text"]});
                font-size: 27px;
                font-weight: 900;
                line-height: 1.15;
                margin-bottom: 8px;
            }}

            .td-card-caption {{
                color: {c["muted"]};
                font-size: 12px;
                line-height: 1.35;
            }}

            .td-alert {{
                background: {c["card"]};
                border: 1px solid {c["border"]};
                border-left: 6px solid var(--accent);
                border-radius: 16px;
                padding: 18px 18px;
                box-shadow: {c["shadow"]};
                margin-bottom: 14px;
            }}

            .td-alert-title {{
                color: {c["text"]};
                font-size: 14px;
                font-weight: 850;
                margin-bottom: 6px;
            }}

            .td-alert-text {{
                color: {c["text"]};
                font-size: 13px;
                line-height: 1.45;
            }}

            hr {{
                margin: 34px 0 !important;
                border-color: {c["border"]} !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def section(titulo, subtitulo):
    st.markdown(
        f"""
        <div class="td-section">
            <h3>{titulo}</h3>
            <p>{subtitulo}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(titulo, valor, legenda, cor, cor_valor=None):
    cor_valor = cor_valor or cores_tema()["text"]

    st.markdown(
        f"""
        <div class="td-card" style="--accent:{cor}; --value-color:{cor_valor};">
            <div class="td-card-label">{titulo}</div>
            <div class="td-card-value">{valor}</div>
            <div class="td-card-caption">{legenda}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def alerta_card(titulo, texto, cor):
    st.markdown(
        f"""
        <div class="td-alert" style="--accent:{cor};">
            <div class="td-alert-title">{titulo}</div>
            <div class="td-alert-text">{texto}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def estilizar_figura(fig):
    c = cores_tema()

    fig.update_layout(
        paper_bgcolor=c["plot_bg"],
        plot_bgcolor=c["plot_bg"],
        font=dict(color=c["plot_font"], size=13),
        margin=dict(l=20, r=30, t=45, b=35),
        xaxis=dict(gridcolor=c["plot_grid"], zeroline=False),
        yaxis=dict(gridcolor=c["plot_grid"], zeroline=False),
    )

    return fig


# ============================================================
# PÁGINA EXECUTIVA
# ============================================================

def exibir_executivo(
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
    resumo_score,
    receita_bairro,
    df_inadimplencia,
    total_ocupados,
    total_vagos,
    total_imoveis,
    contratos_vencendo,
    diagnostico,
    insights,
    card_receita_total,
    card_inadimplencia_imob,
    card_vacancia,
    card_ticket_medio,
    card_contratos,
    grafico_receita_bairro,
    grafico_inadimplencia_bairro,
    grafico_status_imoveis
):

    aplicar_css()

    tipo_classificacao, texto_classificacao = classificar_visual(classificacao)

    VERDE = "#16A34A"
    VERMELHO = "#DC2626"
    LARANJA = "#F59E0B"
    AZUL = "#2563EB"

    if tipo_classificacao == "critica":
        cor_classificacao = VERMELHO
    elif tipo_classificacao == "atencao":
        cor_classificacao = LARANJA
    else:
        cor_classificacao = VERDE

    section(
        "Dashboard executivo",
        "Leitura executiva dos principais riscos, perdas e eficiência da carteira."
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        kpi_card("Score", f"{score}/100", "Saúde geral da carteira", cor_classificacao, cor_classificacao)

    with c2:
        kpi_card("Classificação", texto_classificacao, "Nível de atenção", cor_classificacao, cor_classificacao)

    with c3:
        kpi_card("Receita perdida", moeda_br_negativa(receita_perdida), "Potencial não realizado", VERMELHO, VERMELHO)

    with c4:
        cor_inad_pct = VERMELHO if perc_inadimplencia >= 50 else LARANJA
        kpi_card("Inadimplência", percentual_br(perc_inadimplencia, 1), "Percentual sobre a receita", cor_inad_pct, cor_inad_pct)

    with c5:
        cor_ef = VERDE if eficiencia >= 80 else AZUL
        kpi_card("Eficiência", percentual_br(eficiencia, 1), "Ocupação da carteira", cor_ef, cor_ef)

    st.divider()

    section(
        "Indicadores principais",
        "Números principais da base analisada."
    )

    i1, i2, i3, i4, i5 = st.columns(5)

    with i1:
        kpi_card("Receita", moeda_br(receita), "Receita contratada", VERDE, VERDE)

    with i2:
        kpi_card("Inadimplência", moeda_br_negativa(inadimplencia), "Valor em atraso", VERMELHO, VERMELHO)

    with i3:
        cor_vac = LARANJA if vacancia >= 15 else VERDE
        kpi_card("Vacância", percentual_br(vacancia, 1), "Imóveis vagos", cor_vac, cor_vac)

    with i4:
        kpi_card("Ticket médio", moeda_br(ticket), "Média dos contratos", AZUL)

    with i5:
        kpi_card("Contratos", ativos, "Contratos ativos", AZUL)

    st.divider()

    section(
        "Indicadores estratégicos",
        "Receita e inadimplência por bairro para análise de concentração."
    )

    g1, g2 = st.columns(2)

    with g1:
        fig_receita = grafico_receita_bairro(receita_bairro)
        fig_receita.update_traces(marker_color=AZUL)
        st.plotly_chart(
            estilizar_figura(fig_receita),
            use_container_width=True
        )

    with g2:
        fig_inad = grafico_inadimplencia_bairro(df_inadimplencia)
        fig_inad.update_traces(marker_color=VERMELHO)
        st.plotly_chart(
            estilizar_figura(fig_inad),
            use_container_width=True
        )

    st.divider()

    section(
        "Ocupação dos imóveis",
        "Distribuição entre imóveis ocupados e vagos."
    )

    c1, c2 = st.columns([2, 1])

    with c1:
        fig_status = grafico_status_imoveis(total_ocupados, total_vagos)
        st.plotly_chart(
            estilizar_figura(fig_status),
            use_container_width=True
        )

    with c2:
        m1, m2 = st.columns(2)

        with m1:
            kpi_card("Total", total_imoveis, "Imóveis na base", AZUL)
            kpi_card("Ocupados", total_ocupados, "Imóveis ocupados", VERDE)

        with m2:
            kpi_card("Vagos", total_vagos, "Imóveis vagos", LARANJA if total_vagos > 0 else VERDE)
            kpi_card("Ocupação", percentual_br(eficiencia, 1), "Eficiência atual", AZUL)

    st.divider()

    section(
        "Diagnóstico inteligente",
        "Principais pontos identificados na análise."
    )

    for item in diagnostico:
        texto_item = str(item)

        if "crítico" in texto_item.lower() or "critica" in texto_item.lower():
            alerta_card("Crítico", texto_item, VERMELHO)

        elif "inadimpl" in texto_item.lower() or "vacância" in texto_item.lower() or "vacancia" in texto_item.lower():
            alerta_card("Atenção", texto_item, LARANJA)

        else:
            alerta_card("Diagnóstico", texto_item, AZUL)

    st.divider()

    section(
        "Insights estratégicos",
        "Oportunidades e observações para apoio à decisão."
    )

    for insight in insights:
        alerta_card("Insight", str(insight), VERDE)

    st.divider()

    section(
        "Relatório executivo",
        "Gere o PDF com os principais indicadores, gráficos e parecer executivo."
    )

    if st.button("📄 Gerar Relatório Executivo", use_container_width=True):

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                caminho_pdf = tmp.name

            gerar_pdf_imobiliaria(
                caminho_pdf=caminho_pdf,
                imoveis_totais=total_imoveis,
                imoveis_ocupados=total_ocupados,
                imoveis_vagos=total_vagos,
                vacancia=vacancia,
                ticket_medio=ticket,
                receita=receita,
                inadimplencia=inadimplencia,
                contratos_ativos=ativos,
                contratos_vencendo=contratos_vencendo,
                diagnostico=diagnostico,
                insights=insights,
                receita_bairro=receita_bairro,
                df_inadimplencia=df_inadimplencia,
                score=score,
                classificacao=texto_classificacao,
                receita_perdida=receita_perdida,
                perc_inadimplencia=perc_inadimplencia,
                eficiencia=eficiencia
            )

            with open(caminho_pdf, "rb") as pdf:
                st.download_button(
                    label="⬇️ Baixar PDF",
                    data=pdf.read(),
                    file_name="Relatorio_Imobiliaria.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            try:
                os.remove(caminho_pdf)
            except Exception:
                pass

            st.success("PDF gerado com sucesso.")

        except Exception as erro:
            st.error(f"Não foi possível gerar o PDF: {erro}")