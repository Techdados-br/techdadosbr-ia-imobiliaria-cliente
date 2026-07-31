import streamlit as st

from relatorios.pdf_imobiliaria import gerar_pdf_imobiliaria


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

    st.subheader("📈 Dashboard Executivo")

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        card_receita_total(receita)

    with c2:
        card_inadimplencia_imob(inadimplencia)

    with c3:
        card_vacancia(vacancia)

    with c4:
        card_ticket_medio(ticket)

    with c5:
        card_contratos(ativos)

    st.divider()

    st.subheader("📊 Score Executivo TechDadosBR")

    classificacao_visual = str(classificacao).upper().strip()

    if "CRÍTICA" in classificacao_visual or "CRITICA" in classificacao_visual:
        tipo_classificacao = "critica"
        texto_classificacao = "CRÍTICA"

    elif "ATENÇÃO" in classificacao_visual or "ATENCAO" in classificacao_visual:
        tipo_classificacao = "atencao"
        texto_classificacao = "ATENÇÃO"

    else:
        tipo_classificacao = "saudavel"
        texto_classificacao = "SAUDÁVEL"

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.info(f"⭐ Score\n\n{score}/100")

    with c2:

        if tipo_classificacao == "critica":
            st.error(f"🚦 {texto_classificacao}")

        elif tipo_classificacao == "atencao":
            st.markdown(
                f"""
                <div style="
                     background-color:#F2C94C;
                     color:#000000;
                     padding:18px;
                     border-radius:6px;
                    font-weight:bold;
                ">
                🚦 {texto_classificacao}
                </div>
                """,
                unsafe_allow_html=True
            )

        else:
            st.success(f"🚦 {texto_classificacao}")

    with c3:
        st.success(
            f"💸 Receita Perdida\n\nR$ {receita_perdida:,.0f}"
        )

    with c4:
        st.warning(
            f"⚠️ Inadimplência\n\n{perc_inadimplencia:.1f}%"
        )

    with c5:
        st.info(
            f"🏠 Eficiência\n\n{eficiencia:.1f}%"
        )

    st.subheader("🧠 Resumo Executivo IA")

    c1, c2 = st.columns(2)

    with c1:

        if score >= 80:
            st.success(f"Score Geral: {score}/100")

        elif score >= 60:
            st.warning(f"Score Geral: {score}/100")

        else:
            st.error(f"Score Geral: {score}/100")

    with c2:

        if tipo_classificacao == "critica":
            st.error(
                f"Classificação: {texto_classificacao}"
            )

        elif tipo_classificacao == "atencao":
            st.markdown(
                f"""
                <div style="
                    background-color:#F2C94C;
                    color:#000000;
                    padding:18px;
                    border-radius:6px;
                    font-weight:bold;
                 ">
                Classificação: {texto_classificacao}
                </div>
                 """,
                unsafe_allow_html=True
            )
           
        else:
            st.success(
                f"Classificação: {texto_classificacao}"
            )

    st.divider()

    st.subheader("📊 Indicadores Estratégicos")

    g1, g2 = st.columns(2)

    with g1:
        st.plotly_chart(
            grafico_receita_bairro(
                receita_bairro
            ),
            use_container_width=True
        )

    with g2:
        st.plotly_chart(
            grafico_inadimplencia_bairro(
                df_inadimplencia
            ),
            use_container_width=True
        )

    st.divider()

    st.subheader("🏠 Ocupação dos Imóveis")

    c1, c2 = st.columns([2, 1])

    with c1:

        st.plotly_chart(
            grafico_status_imoveis(
                total_ocupados,
                total_vagos
            ),
            use_container_width=True
        )

    with c2:

        m1, m2 = st.columns(2)

        with m1:
            st.metric(
                "🏢 Total",
                total_imoveis
            )

            st.metric(
                "✅ Ocupados",
                total_ocupados
            )

        with m2:
            st.metric(
                "⚠️ Vagos",
                total_vagos
            )

            st.metric(
                "📈 Ocupação",
                f"{eficiencia:.1f}%"
            )

    st.divider()

    st.subheader("🤖 Diagnóstico Inteligente")

    for item in diagnostico:

        if "crítico" in item.lower():
            st.error(item)

        elif "inadimpl" in item.lower():
            st.warning(item)

        else:
            st.info(item)

    st.divider()

    st.subheader("💡 Insights Estratégicos")

    for insight in insights:
        st.success(insight)

    st.divider()

    st.subheader("📄 Relatório Executivo")

    if st.button(
        "📄 Gerar Relatório Executivo"
    ):

        caminho_pdf = "Relatorio_Imobiliaria.pdf"

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

        with open(
            caminho_pdf,
            "rb"
        ) as pdf:

            st.download_button(
                label="⬇️ Baixar PDF",
                data=pdf,
                file_name="Relatorio_Imobiliaria.pdf",
                mime="application/pdf"
            )

        st.success(
            "PDF gerado com sucesso."
        )