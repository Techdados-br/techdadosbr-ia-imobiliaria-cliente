import streamlit as st


def card_saude(saude):

    cor = "#16a34a"

    if saude == "Regular":
        cor = "#f59e0b"

    if saude == "Crítica":
        cor = "#dc2626"

    st.markdown(
        f"""
        <div style="
            background:{cor};
            padding:20px;
            border-radius:15px;
            text-align:center;
            color:white;
        ">
            <h4>Saúde Financeira</h4>
            <h2>{saude}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )


def card_situacao(situacao):

    cor = "#16a34a"

    if situacao == "Déficit":
        cor = "#dc2626"

    st.markdown(
        f"""
        <div style="
            background:{cor};
            padding:20px;
            border-radius:15px;
            text-align:center;
            color:white;
        ">
            <h4>Situação</h4>
            <h2>{situacao}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )


def card_dependencia(percentual):

    cor = "#16a34a"

    if percentual > 15:
        cor = "#f59e0b"

    if percentual > 30:
        cor = "#dc2626"

    st.markdown(
        f"""
        <div style="
            background:{cor};
            padding:20px;
            border-radius:15px;
            text-align:center;
            color:white;
        ">
            <h4>Dependência</h4>
            <h2>{percentual:.1f}%</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

