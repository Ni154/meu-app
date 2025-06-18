import streamlit as st
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import pandas as pd
import plotly.express as px
import uuid

# Inicializa banco de dados
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
    status TEXT DEFAULT 'Ativa',
    pedido_id TEXT
)
""")

conn.commit()

# Cria um usuário padrão se não existir
cursor.execute("SELECT COUNT(*) FROM usuarios")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ("admin", "1234"))
    conn.commit()

# Configurações de tema
if "cor_fundo" not in st.session_state:
    st.session_state.cor_fundo = "#FFFFFF"  # Branco padrão
if "cor_menu" not in st.session_state:
    st.session_state.cor_menu = "#F9A825"  # Amarelo mostarda padrão
if "show_config" not in st.session_state:
    st.session_state.show_config = False
if "logado" not in st.session_state:
    st.session_state.logado = False

def aplicar_estilos():
    st.markdown(f"""
    <style>
    /* Fundo da aplicação */
    .css-1d391kg {{
        background-color: {st.session_state.cor_fundo} !important;
    }}
    /* Menu lateral */
    .css-1v3fvcr {{
        background-color: {st.session_state.cor_menu} !important;
    }}
    /* Botão personalizado */
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
    /* Sidebar container */
    .sidebar .block-container {{
        background-color: rgba(255, 255, 255, 0.8);
        padding: 10px;
        border-radius: 10px;
    }}
    /* Ícone configuração fixo topo direito */
    #botao_config {{
        position: fixed;
        top: 10px;
        right: 10px;
        font-size: 25px;
        cursor: pointer;
        z-index: 9999;
        color: #FF8C00;
    }}
    </style>
    """, unsafe_allow_html=True)

def painel_configuracoes():
    st.subheader("⚙️ Configurações")

    cor_fundo = st.color_picker("Cor do Fundo", st.session_state.cor_fundo)
    cor_menu = st.color_picker("Cor do Menu Lateral", st.session_state.cor_menu)

    if st.button("Aplicar cores"):
        st.session_state.cor_fundo = cor_fundo
        st.session_state.cor_menu = cor_menu
        st.experimental_rerun()

def pagina_login():
    st.markdown("""
        <style>
        .login_logo {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
    logo_upload = st.file_uploader("Faça upload da logo da empresa (PNG, JPG)", type=["png", "jpg", "jpeg"], key="logo_login")
    if logo_upload:
        st.image(logo_upload, width=200)
        st.session_state.logo = logo_upload

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

def pagina_inicio():
    st.subheader("🍔 Bem-vindo ao sistema de vendas NS Lanches")
    st.write("Utilize o menu lateral para navegar entre as funcionalidades.")

# ... (Você pode incluir as outras funções que deseja para o cadastro, vendas, relatórios, cancelamento aqui)

def main():
    st.set_page_config(layout="wide", page_title="NS Lanches")
    aplicar_estilos()

    if not st.session_state.logado:
        pagina_login()
        return

    # Ícone fixo para abrir/fechar configurações
    if st.button("⚙️", key="botao_config"):
        st.session_state.show_config = not st.session_state.show_config

    # Sidebar para navegação
    with st.sidebar:
        st.title("Menu")
        pagina = st.radio("Escolha a página", ["Início", "Configurações"])
        if pagina == "Início":
            pagina_inicio()
        elif pagina == "Configurações":
            painel_configuracoes()

    # Painel de configurações flutuante
    if st.session_state.show_config:
        with st.sidebar.expander("Configurações Avançadas", expanded=True):
            painel_configuracoes()

if __name__ == "__main__":
    main()
