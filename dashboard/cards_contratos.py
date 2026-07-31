import streamlit as st


def moeda_br(valor):

    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def card_contrato(titulo, valor):

    st.markdown(
        f"""
<div style="
background-color:#111827;
padding:20px;
border-radius:15px;
border:2px solid #2563eb;
text-align:center;
margin-bottom:10px;">

<h4 style="color:#60a5fa;">
{titulo}
</h4>

<h2 style="color:white;">
{valor}
</h2>

</div>
""",
        unsafe_allow_html=True
    )


def card_total_contratos(valor):

    card_contrato(
        "📊 Total Contratos",
        valor
    )


def card_contratos_ativos(valor):

    card_contrato(
        "📄 Contratos Ativos",
        valor
    )


def card_contratos_vencendo(valor):

    card_contrato(
        "📅 Contratos Vencendo",
        valor
    )


def card_valor_medio_contrato(valor):

    card_contrato(
        "💰 Valor Médio",
        moeda_br(valor)
    )