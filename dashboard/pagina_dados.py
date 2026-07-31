import streamlit as st


def exibir_dados(
    df_imoveis,
    df_contratos,
    df_receitas,
    df_inadimplencia
):

    st.subheader("⚙️ Dados")

    with st.expander(
        "Colunas Normalizadas"
    ):

        st.write(
            list(df_imoveis.columns)
        )

    with st.expander(
        "Imóveis"
    ):

        st.dataframe(
            df_imoveis,
            use_container_width=True
        )

    with st.expander(
        "Contratos"
    ):

        st.dataframe(
            df_contratos,
            use_container_width=True
        )

    with st.expander(
        "Receitas"
    ):

        st.dataframe(
            df_receitas,
            use_container_width=True
        )

    with st.expander(
        "Inadimplência"
    ):

        st.dataframe(
            df_inadimplencia,
            use_container_width=True
        )