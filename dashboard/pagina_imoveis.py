import streamlit as st


def exibir_imoveis(
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
):

    st.subheader("🏢 Gestão de Imóveis")

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        card_imoveis_totais(total_imoveis)

    with c2:
        card_imoveis_ocupados(total_ocupados)

    with c3:
        card_imoveis_vagos(total_vagos)

    with c4:
        card_vacancia(vacancia)

    with c5:
        card_ticket_medio(ticket)

    st.divider()

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
            grafico_ranking_corretores(
                ranking
            ),
            use_container_width=True
        )

    st.divider()

    st.plotly_chart(
        grafico_status_imoveis(
            total_ocupados,
            total_vagos
        ),
        use_container_width=True
    )

    st.divider()

    st.subheader("📋 Cadastro de Imóveis")

    st.dataframe(
        df_imoveis,
        use_container_width=True
    )