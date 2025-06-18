import streamlit as st
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import pandas as pd
import plotly.express as px
import uuid

# Conexao com banco de dados
conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# Cria tabelas se não existirem
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL,
    senha TEXT NOT NULL
)
""")
cursor.execute("SELECT COUNT(*) FROM usuarios")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ("admin", "1234"))
    conn.commit()

# Cria outras tabelas
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
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    produto TEXT,
    cliente TEXT,
    quantidade INTEGER,
    total REAL,
    status TEXT DEFAULT 'Ativa',
    pedido_id TEXT
)
""")
conn.commit()

# Estado inicial
if "logado" not in st.session_state:
    st.session_state.logado = False
if "cor_fundo" not in st.session_state:
    st.session_state.cor_fundo = "#FFFFFF"
if "cor_menu" not in st.session_state:
    st.session_state.cor_menu = "#F9A825"
if "pagina" not in st.session_state:
    st.session_state.pagina = "Início"

# Estilos
st.set_page_config(layout="wide", page_title="NS Lanches")
st.markdown(f"""
    <style>
        .stApp {{
            background-color: {st.session_state.cor_fundo};
        }}
        .css-1d391kg {{
            background-color: {st.session_state.cor_menu};
        }}
        .stButton>button {{
            background-color: #FF8C00;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 16px;
            margin-bottom: 10px;
        }}
        .stButton>button:hover {{
            background-color: #e67e00;
        }}
        .sidebar .block-container {{
            background-color: rgba(255, 255, 255, 0.8);
            padding: 10px;
            border-radius: 10px;
        }}
    </style>
""", unsafe_allow_html=True)

# Painel de configurações de cor
with st.sidebar:
    st.markdown("---")
    st.subheader("⚙️ Configurações")
    cor_fundo = st.color_picker("Cor do Fundo", st.session_state.cor_fundo)
    cor_menu = st.color_picker("Cor do Menu Lateral", st.session_state.cor_menu)
    if st.button("Aplicar cores"):
        st.session_state.cor_fundo = cor_fundo
        st.session_state.cor_menu = cor_menu
        st.experimental_rerun()

# Página de login
def pagina_login():
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

# Página inicial

def pagina_inicio():
    st.subheader("🍔 Bem-vindo ao sistema de vendas NS Lanches")
    st.write("Utilize o menu lateral para navegar entre as funcionalidades.")

def pagina_empresa():
    st.subheader("🏢 Cadastro de Empresa")
    # Conteúdo omitido para foco

def pagina_clientes():
    st.subheader("👥 Cadastro de Clientes")
    # Conteúdo omitido para foco

def pagina_produtos():
    st.subheader("🍟 Cadastro de Produtos")
    # Conteúdo omitido para foco

def pagina_vendas():
    st.subheader("🧾 Registrar Venda")
    # Conteúdo omitido para foco

def pagina_cancelar_venda():
    st.subheader("❌ Cancelar Venda")
    # Conteúdo omitido para foco

def pagina_relatorios():
    st.subheader("📊 Relatórios")
    # Conteúdo omitido para foco

# Executa login se necessário
if not st.session_state.logado:
    pagina_login()

# Menu lateral
with st.sidebar:
    st.title("🍟 NS Lanches")
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

# Exibir página selecionada
pagina = st.session_state.get("pagina", "Início")
if pagina == "Início":
    pagina_inicio()
elif pagina == "Empresa":
    pagina_empresa()
elif pagina == "Clientes":
    pagina_clientes()
elif pagina == "Produtos":
    pagina_produtos()
elif pagina == "Vendas":
    pagina_vendas()
elif pagina == "Cancelar Venda":
    pagina_cancelar_venda()
elif pagina == "Relatórios":
    pagina_relatorios()
