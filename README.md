import streamlit as st
import pandas as pd
from datetime import datetime
import os
from fpdf import FPDF

# Arquivo Excel
FILE_PRODUTOS = "produtos.xlsx"
FILE_VENDAS = "vendas.xlsx"

# Função para carregar ou criar DataFrames
def carregar_dados(arquivo, colunas):
    if os.path.exists(arquivo):
        return pd.read_excel(arquivo)
    else:
        return pd.DataFrame(columns=colunas)

# Inicializa os dados
df_produtos = carregar_dados(FILE_PRODUTOS, ["Nome", "Preço", "Estoque", "Categoria", "Data"])
df_vendas = carregar_dados(FILE_VENDAS, ["Data", "Produto", "Quantidade", "Total"])

st.title("Sistema PDV Web")

aba = st.sidebar.selectbox("Menu", ["Cadastro de Produtos", "Vendas", "Relatórios"])

# Cadastro de Produtos
if aba == "Cadastro de Produtos":
    st.subheader("Cadastrar Novo Produto")
    nome = st.text_input("Nome do Produto")
    preco = st.number_input("Preço", min_value=0.0, step=0.01)
    estoque = st.number_input("Quantidade em Estoque", min_value=0, step=1)
    categoria = st.text_input("Categoria")
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if st.button("Cadastrar"):
        novo = {"Nome": nome, "Preço": preco, "Estoque": estoque, "Categoria": categoria, "Data": data}
        df_produtos = pd.concat([df_produtos, pd.DataFrame([novo])], ignore_index=True)
        df_produtos.to_excel(FILE_PRODUTOS, index=False)
        st.success("Produto cadastrado com sucesso!")

    st.subheader("Produtos Cadastrados")
    st.dataframe(df_produtos)

# Vendas
elif aba == "Vendas":
    st.subheader("Registrar Venda")
    produtos = df_produtos["Nome"].tolist()

    if produtos:
        produto = st.selectbox("Produto", produtos)
        quantidade = st.number_input("Quantidade", min_value=1, step=1)

        if st.button("Finalizar Venda"):
            produto_info = df_produtos[df_produtos["Nome"] == produto].iloc[0]
            if quantidade > produto_info["Estoque"]:
                st.warning("Estoque insuficiente!")
            else:
                total = quantidade * produto_info["Preço"]
                data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Atualizar estoque
                df_produtos.loc[df_produtos["Nome"] == produto, "Estoque"] -= quantidade
                df_produtos.to_excel(FILE_PRODUTOS, index=False)

                # Salvar venda
                venda = {"Data": data_venda, "Produto": produto, "Quantidade": quantidade, "Total": total}
                df_vendas = pd.concat([df_vendas, pd.DataFrame([venda])], ignore_index=True)
                df_vendas.to_excel(FILE_VENDAS, index=False)

                # Gerar comprovante
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt="Comprovante de Venda", ln=1, align="C")
                pdf.cell(200, 10, txt=f"Data: {data_venda}", ln=2)
                pdf.cell(200, 10, txt=f"Produto: {produto}", ln=3)
                pdf.cell(200, 10, txt=f"Quantidade: {quantidade}", ln=4)
                pdf.cell(200, 10, txt=f"Total: R$ {total:.2f}", ln=5)
                nome_pdf = f"comprovante_{produto}{data_venda.replace(':', '-').replace(' ', '')}.pdf"
                pdf.output(nome_pdf)

                with open(nome_pdf, "rb") as file:
                    btn = st.download_button(
                        label="Baixar Comprovante em PDF",
                        data=file,
                        file_name=nome_pdf,
                        mime="application/pdf"
                    )

                st.success("Venda registrada com sucesso!")
    else:
        st.warning("Cadastre produtos primeiro.")

# Relatórios
elif aba == "Relatórios":
    st.subheader("Relatório de Vendas")
    filtro_produto = st.selectbox("Filtrar por Produto", ["Todos"] + df_vendas["Produto"].unique().tolist())

    if filtro_produto != "Todos":
        df_filtrado = df_vendas[df_vendas["Produto"] == filtro_produto]
    else:
        df_filtrado = df_vendas

    st.dataframe(df_filtrado)

    total_vendas = df_filtrado["Total"].sum()
    st.info(f"Total vendido: R$ {total_vendas:.2f}")
    # meu-app
