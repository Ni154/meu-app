# sistema_pdv_streamlit.py
import streamlit as st
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import os
import pandas as pd
import plotly.express as px

# Conexão com o banco de dados
conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# Criação das tabelas (caso não existam)
cursor.execute("""
CREATE TABLE IF NOT EXISTS empresa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cnpj TEXT NOT NULL
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL,
    senha TEXT NOT NULL
)""")

cursor.execute("SELECT COUNT(*) FROM usuarios")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ("admin", "1234"))
    conn.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT,
    telefone TEXT,
    endereco TEXT
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    preco REAL,
    estoque INTEGER,
    unidade TEXT,
    categoria TEXT,
    data TEXT
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    produto TEXT,
    cliente TEXT,
    quantidade INTEGER,
    total REAL
)""")
conn.commit()

# Função para adicionar imagem de fundo
def adicionar_plano_de_fundo(imagem_url):
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url('{imagem_url}');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        .stButton > button {{
            background-color: orange;
            color: white;
            border-radius: 10px;
            padding: 0.5em 1em;
            border: none;
        }}
        </style>
    """, unsafe_allow_html=True)

# Estado inicial
if "logado" not in st.session_state:
    st.session_state.logado = False
if "pagina" not in st.session_state:
    st.session_state.pagina = "Início"
if "logo" not in st.session_state:
    st.session_state.logo = None

# Login
if not st.session_state.logado:
    st.title("NS Sistemas - Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
        if cursor.fetchone():
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos")
            st.stop()

# Se logado, mostra o sistema
else:
    # Fundo personalizado (pode usar uma URL de imagem)
    adicionar_plano_de_fundo("https://i.imgur.com/fd7hJ8w.jpg")  # Substitua pela sua imagem

    with st.sidebar:
        st.title("NS Sistemas")
        st.session_state.logo = st.file_uploader("Logo da empresa", type=["png", "jpg", "jpeg"])
        if st.button("Início"): st.session_state.pagina = "Início"
        if st.button("Empresa"): st.session_state.pagina = "Empresa"
        if st.button("Clientes"): st.session_state.pagina = "Clientes"
        if st.button("Produtos"): st.session_state.pagina = "Produtos"
        if st.button("Vendas"): st.session_state.pagina = "Vendas"
        if st.button("Cancelar Venda"): st.session_state.pagina = "Cancelar Venda"
        if st.button("Relatórios"): st.session_state.pagina = "Relatórios"

    if st.session_state.logo:
        try:
            st.image(st.session_state.logo, width=250)
        except:
            st.warning("Erro ao carregar a logo.")

    # Exibe dados da empresa
    cursor.execute("SELECT nome, cnpj FROM empresa ORDER BY id DESC LIMIT 1")
    dados_empresa = cursor.fetchone()
    if dados_empresa:
        st.markdown(f"### Empresa: {dados_empresa[0]}")
        st.markdown(f"**CNPJ:** {dados_empresa[1]}")
    else:
        st.warning("Nenhuma empresa cadastrada.")


