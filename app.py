import streamlit as st
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import os
import pandas as pd
import plotly.express as px

# Inicializa banco de dados
conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# Funções de páginas
def pagina_inicio():
    st.subheader("Bem-vindo ao sistema de vendas NS Sistemas")
    st.write("Utilize o menu lateral para navegar entre as funcionalidades.")

def pagina_empresa():
    st.subheader("Cadastrar Empresa")
    nome_empresa = st.text_input("Nome da Empresa")
    cnpj_empresa = st.text_input("CNPJ")
    if st.button("Salvar Empresa"):
        if nome_empresa and cnpj_empresa:
            try:
                cursor.execute("INSERT INTO empresa (nome, cnpj) VALUES (?, ?)", (nome_empresa, cnpj_empresa))
                conn.commit()
                st.success("Empresa cadastrada com sucesso!")
            except Exception as e:
                st.error(f"Erro ao cadastrar empresa: {e}")
        else:
            st.warning("Preencha todos os campos.")

def pagina_clientes():
    st.subheader("Cadastro de Cliente")
    nome = st.text_input("Nome")
    cpf = st.text_input("CPF")
    telefone = st.text_input("Telefone")
    endereco = st.text_area("Endereço (Rua, Número, Apto...)")
    if st.button("Cadastrar Cliente"):
        if nome:
            try:
                cursor.execute("INSERT INTO clientes (nome, cpf, telefone, endereco) VALUES (?, ?, ?, ?)", (nome, cpf, telefone, endereco))
                conn.commit()
                st.success("Cliente cadastrado com sucesso")
            except Exception as e:
                st.error(f"Erro ao cadastrar cliente: {e}")
        else:
            st.warning("Informe o nome do cliente")

def pagina_produtos():
    st.subheader("Cadastro de Produtos")
    nome = st.text_input("Nome do Produto")
    preco = st.number_input("Preço", step=0.01)
    estoque = st.number_input("Estoque", step=1)
    unidade = st.selectbox("Unidade", ["Unidade", "Peso"])
    categoria = st.text_input("Categoria")
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if st.button("Cadastrar Produto"):
        if nome and preco >= 0:
            try:
                cursor.execute("INSERT INTO produtos (nome, preco, estoque, unidade, categoria, data) VALUES (?, ?, ?, ?, ?, ?)",
                    (nome, preco, estoque, unidade, categoria, data))
                conn.commit()
                st.success("Produto cadastrado com sucesso")
            except Exception as e:
                st.error(f"Erro ao cadastrar produto: {e}")
        else:
            st.warning("Preencha os campos obrigatórios.")

# Configurações iniciais da página
st.set_page_config(layout="wide")
st.markdown(
    """
    <style>
    .stButton>button {
        background-color: #FFA500;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 16px;
        margin-bottom: 8px;
    }
    .stButton>button:hover {
        background-color: #FF8C00;
    }
    .sidebar-content {
        background-image: url('https://img.freepik.com/vetores-gratis/fundo-de-grade-azul-gradiente_23-2149333607.jpg');
        background-size: cover;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if "pagina" not in st.session_state:
    st.session_state.pagina = "Início"
if "logo" not in st.session_state:
    st.session_state.logo = None

# Sidebar
with st.sidebar:
    st.title("NS Sistemas")
    st.session_state.logo = st.file_uploader("Logo da empresa", type=["png", "jpg", "jpeg"])
    if st.session_state.logo:
        st.image(st.session_state.logo, width=250)
    if st.button("Início"):
        st.session_state.pagina = "Início"
    if st.button("Empresa"):
        st.session_state.pagina = "Empresa"
    if st.button("Clientes"):
        st.session_state.pagina = "Clientes"
    if st.button("Produtos"):
        st.session_state.pagina = "Produtos"
    if st.button("Vendas"):
        st.session_state.pagina = "Vendas"
    if st.button("Cancelar Venda"):
        st.session_state.pagina = "Cancelar Venda"
    if st.button("Relatórios"):
        st.session_state.pagina = "Relatórios"

# Exibição da página selecionada
pagina = st.session_state.pagina
if pagina == "Início":
    pagina_inicio()
elif pagina == "Empresa":
    pagina_empresa()
elif pagina == "Clientes":
    pagina_clientes()
elif pagina == "Produtos":
    pagina_produtos()
# Continuar implementando as demais páginas com base nas funções originais
