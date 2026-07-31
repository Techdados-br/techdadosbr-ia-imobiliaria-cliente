import streamlit as st


def moeda_br(valor):

    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def card_premium(titulo, valor):

    st.markdown(
        f"""
<div style="
background-color:#111827;
padding:28px;
border-radius:18px;
border:2px solid #3b82f6;
ox-shadow: 0px 0px 15px rgba(59,130,246,0.35);

<h4 style="
color:#93c5fd;
font-size:18px;
font-weight:
{titulo}
</h4>

<h2 style="
color:white;
font-size:34px;
font-weight:700;
margin-top:10px;
">
{valor}
</h2>

</div>
""",
        unsafe_allow_html=True
    )


def card_imoveis_totais(valor):
    card_premium("🏠 Imóveis Totais", valor)


def card_imoveis_ocupados(valor):
    card_premium("🔑 Imóveis Ocupados", valor)


def card_imoveis_vagos(valor):
    card_premium("🚪 Imóveis Vagos", valor)


def card_vacancia(valor):
    card_premium(
        "📈 Vacância %",
        f"{valor:.2f}%".replace(".", ",")
    )


def card_ticket_medio(valor):
    card_premium(
        "💰 Ticket Médio",
        moeda_br(valor)
    )


def card_corretores(valor):
    card_premium(
        "👨‍💼 Corretores",
        valor
    )


def card_contratos(valor):
    card_premium(
        "📄 Contratos Ativos",
        valor
    )


def card_inadimplencia_imob(valor):
    card_premium(
        "⚠️ Inadimplência",
        moeda_br(valor)
    )


def card_receita_total(valor):
    card_premium(
        "💵 Receita Total",
        moeda_br(valor)
    )


def card_contratos_vencendo(valor):
    card_premium(
        "📅 Contratos Vencendo",
        valor
    )