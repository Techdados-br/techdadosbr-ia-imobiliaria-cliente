import streamlit as st


def exibir_insights(
    df_imoveis,
    gerar_insights_imobiliarios,
    gerar_diagnostico_imobiliario
):
    st.write("TESTE INSIGHTS")

    st.subheader(
        "🤖 Central de Inteligência Imobiliária"
    )

    insights = gerar_insights_imobiliarios(
        df_imoveis
    )

    diagnostico = gerar_diagnostico_imobiliario(
        df_imoveis
    )

    st.markdown("### 🟢 Situação Geral da Operação")

    for insight in insights:

        st.success(
            insight
        )

    st.divider()

    st.markdown("### 🟡 Pontos de Atenção")

    if len(diagnostico) > 0:

        for item in diagnostico:

            st.warning(
                item
            )

    else:

        st.success(
            "Nenhum risco identificado."
        )

    st.divider()

    st.markdown("### 📈 Recomendações Estratégicas")

    st.info(
        """
• Monitorar imóveis vagos para aumentar a ocupação.

• Acompanhar contratos próximos do vencimento.

• Reduzir índices de inadimplência.

• Concentrar esforços comerciais nos bairros mais rentáveis.

• Reforçar ações dos corretores com melhor desempenho.
"""
    )

    st.divider()

    st.markdown("### 🚀 Resumo Executivo")

    st.success(
        """
A TechDadosBR AI analisou automaticamente os dados da imobiliária e identificou oportunidades de melhoria operacional, financeira e comercial.

Utilize os indicadores das páginas anteriores para acompanhar vacância, inadimplência, contratos e desempenho dos bairros.
"""
    )