# SISTEMA NS LANCHES COMPLETO COM PERSONALIZAÇÃO DE TEMA
import streamlit as st
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import os
import pandas as pd
import plotly.express as px
from PIL import Image

# Conexão com banco
conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# Criação das tabelas se não existirem
cursor.execute("""
CREATE TABLE IF NOT EXISTS empresa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cnpj TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT,
    telefone TEXT,
    endereco TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    preco REAL,
    estoque INTEGER,
    unidade TEXT,
    categoria TEXT,
    data TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL,
    senha TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    produto TEXT,
    cliente TEXT,
    quantidade INTEGER,
    total REAL,
    cancelada INTEGER DEFAULT 0
)
""")

conn.commit()

# Cria um usuário padrão se não existir
cursor.execute("SELECT COUNT(*) FROM usuarios")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ("admin", "1234"))
    conn.commit()

# -------------------------- TEMAS --------------------------
if "tema_cor" not in st.session_state:
    st.session_state.tema_cor = "laranja"

temas = {
    "laranja": {"fundo": "#FFF3E0", "menu": "#FF8C00"},
    "azul": {"fundo": "#E3F2FD", "menu": "#2196F3"},
    "verde": {"fundo": "#E8F5E9", "menu": "#4CAF50"},
    "preto": {"fundo": "#212121", "menu": "#424242"},
    "amarelo": {"fundo": "#FFFDE7", "menu": "#FBC02D"},
}

cor_fundo = temas[st.session_state.tema_cor]["fundo"]
cor_menu = temas[st.session_state.tema_cor]["menu"]

st.set_page_config(layout="wide", page_title="NS Lanches")
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {cor_fundo};
    }}
    .stButton>button {{
        background-color: {cor_menu};
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 16px;
        margin-bottom: 10px;
    }}
    .stButton>button:hover {{
        background-color: #888;
    }}
    .sidebar .block-container {{
        background-color: {cor_menu};
        padding: 10px;
        border-radius: 10px;
    }}
    </style>
""", unsafe_allow_html=True)

# ---------------------- LOGIN --------------------------
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("logo.png", width=200)

    with st.expander("⚙ Configurações de Tema"):
        nova_cor = st.selectbox("Escolha o tema do sistema:", list(temas.keys()), index=list(temas.keys()).index(st.session_state.tema_cor))
        if nova_cor != st.session_state.tema_cor:
            st.session_state.tema_cor = nova_cor
            st.experimental_rerun()

    st.title("🍔 NS Lanches - Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
        if cursor.fetchone():
            st.session_state.logado = True
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos")
    st.stop()

# O restante do seu código de páginas e funcionalidades segue abaixo sem alterações
