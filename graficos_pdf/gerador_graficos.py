import matplotlib.pyplot as plt

def salvar_grafico_receita_bairro(df):

    plt.figure(figsize=(10, 6))

    ax = df.plot(
        x="bairro",
        y="valor_aluguel",
        kind="barh",
        legend=False
    )

    plt.title(
        "Receita por Bairro",
        fontsize=14,
        fontweight="bold"
    )

    for i, valor in enumerate(df["valor_aluguel"]):

        ax.text(
            valor,
            i,
            f" R$ {valor:,.0f}",
            va="center"
        )

    plt.tight_layout()

    plt.savefig(
        "assets/grafico_receita.png",
        dpi=300
    )

    plt.close()

def salvar_grafico_inadimplencia(df):

    dados = (
        df.groupby("Bairro")["Valor_Atrasado"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    plt.figure(figsize=(10, 6))

    ax = dados.plot(
        kind="barh"
    )

    plt.title(
        "Top 10 Bairros com Maior Inadimplência",
        fontsize=14,
        fontweight="bold"
    )

    plt.xlabel(
        "Valor em Atraso (R$)"
    )

    plt.ylabel("")

    for i, valor in enumerate(dados):

        ax.text(
            valor,
            i,
            f" R$ {valor:,.0f}",
            va="center"
        )

    plt.tight_layout()

    plt.savefig(
        "assets/grafico_inadimplencia.png",
        dpi=300
    )

    plt.close()

def salvar_grafico_vacancia(
    ocupados,
    vagos
):

    plt.figure(figsize=(10, 4))

    categorias = [
        "Ocupados",
        "Vagos"
    ]

    valores = [
        ocupados,
        vagos
    ]

    plt.barh(
        categorias,
        valores
    )

    plt.title(
        "Status dos Imóveis"
    )

    for i, valor in enumerate(valores):

        plt.text(
            valor + 1,
            i,
            str(valor)
        )

    plt.tight_layout()

    plt.savefig(
        "assets/grafico_vacancia.png",
        dpi=300
    )

    plt.close()