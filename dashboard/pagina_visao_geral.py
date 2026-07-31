import streamlit as st


def exibir_visao_geral(
    total_imoveis,
    total_ocupados,
    total_vagos,
    vacancia,
    ticket,
    receita,
    inadimplencia,
    ativos,
    vencendo,
    receita_bairro,
    ranking,
    card_imoveis_totais,
    card_imoveis_ocupados,
    card_imoveis_vagos,
    card_vacancia,
    card_ticket_medio,
    card_receita_total,
    card_inadimplencia_imob,
    card_contratos,
    card_contratos_vencendo,
    grafico_receita_bairro,
    grafico_ranking_corretores,
    grafico_status_imoveis
):

    st.subheader("📊 Indicadores Imobiliários")

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

    st.subheader("💰 Indicadores Financeiros")

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        card_receita_total(receita)

    with f2:
        card_inadimplencia_imob(inadimplencia)

    with f3:
        card_contratos(ativos)

    with f4:
        card_contratos_vencendo(vencendo)

    st.divider()

    g1, g2 = st.columns(2)

    with g1:
        st.plotly_chart(
            grafico_receita_bairro(receita_bairro),
            use_container_width=True
        )

    with g2:
        st.plotly_chart(
            grafico_ranking_corretores(ranking),
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