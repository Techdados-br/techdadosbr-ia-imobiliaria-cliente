import streamlit as st


def exibir_riscos(
    df_inadimplencia,
    grafico_top_inadimplentes,
    grafico_inadimplencia_bairro
):

    st.subheader(
        "⚠️ Central de Riscos Financeiros"
    )

    r1, r2 = st.columns(2)

    with r1:

        st.plotly_chart(
            grafico_top_inadimplentes(
                df_inadimplencia
            ),
            use_container_width=True
        )

    with r2:

        st.plotly_chart(
            grafico_inadimplencia_bairro(
                df_inadimplencia
            ),
            use_container_width=True
        )