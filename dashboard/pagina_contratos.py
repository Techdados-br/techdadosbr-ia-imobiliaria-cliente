import streamlit as st


def exibir_contratos(
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
):

    st.subheader("📄 Gestão de Contratos")

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        card_total_contratos(
            total_ctr
        )

    with k2:
        card_contratos_ativos(
            ativos
        )

    with k3:
        card_contratos_vencendo(
            len(vencendo_df)
        )

    with k4:
        card_valor_medio_contrato(
            valor_medio_ctr
        )

    st.divider()

    g1, g2 = st.columns(2)

    with g1:
        st.plotly_chart(
            grafico_contratos_status(
                status_ctr
            ),
            use_container_width=True
        )

    with g2:
        st.plotly_chart(
            grafico_top_contratos(
                top_ctr
            ),
            use_container_width=True
        )

    st.divider()

    st.plotly_chart(
        grafico_contratos_vencendo(
            vencendo_df
        ),
        use_container_width=True
    )

    st.divider()

    if len(alertas_ctr) > 0:

        st.subheader(
            "🚨 Alertas de Contratos"
        )

        for alerta in alertas_ctr:

            st.warning(
                alerta
            )