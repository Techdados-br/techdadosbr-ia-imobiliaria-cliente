import streamlit as st


def aplicar_filtros(
    df_imoveis,
    df_contratos,
    df_inadimplencia
):

    col_status = None

    for col in df_contratos.columns:

        if str(col).lower() == "status":

            col_status = col
            break

    bairro = st.sidebar.selectbox(
        "🏢 Bairro",
        ["Todos"] + sorted(
            df_imoveis["bairro"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
    )

    corretor = st.sidebar.selectbox(
        "👨‍💼 Corretor",
        ["Todos"] + sorted(
            df_imoveis["corretor"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
    )

    if col_status:

        status = st.sidebar.selectbox(
            "📄 Status",
            ["Todos"] + sorted(
                df_contratos[col_status]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        )

    else:

        status = "Todos"

    if bairro != "Todos":

        df_imoveis = df_imoveis[
            df_imoveis["bairro"] == bairro
        ]

        if "bairro" in df_inadimplencia.columns:

            df_inadimplencia = (
                df_inadimplencia[
                    df_inadimplencia["bairro"]
                    == bairro
                ]
            )

    if corretor != "Todos":

        df_imoveis = df_imoveis[
            df_imoveis["corretor"]
            == corretor
        ]

    if status != "Todos" and col_status:

        df_contratos = df_contratos[
            df_contratos[col_status]
            == status
        ]

    return (
        df_imoveis,
        df_contratos,
        df_inadimplencia
    )