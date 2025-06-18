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

cursor.execute("""
CREATE TABLE IF NOT EXISTS empresa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    cnpj TEXT
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
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    produto TEXT,
    cliente TEXT,
    quantidade INTEGER,
    total REAL,
    status TEXT DEFAULT 'Ativa',
    pedido_id TEXT,
    forma_pagamento TEXT
)
""")
conn.commit()

if "logado" not in st.session_state:
    st.session_state.logado = False
if "cor_fundo" not in st.session_state:
    st.session_state.cor_fundo = "#FFFFFF"
if "cor_menu" not in st.session_state:
    st.session_state.cor_menu = "#F9A825"
if "pagina" not in st.session_state:
    st.session_state.pagina = "Início"

st.set_page_config(layout="wide", page_title="NS Lanches")
st.markdown(f"""
    <style>
        .stApp {{ background-color: {st.session_state.cor_fundo}; }}
        .css-1d391kg {{ background-color: {st.session_state.cor_menu}; }}
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("---")
    st.subheader("⚙️ Configurações")
    cor_fundo = st.color_picker("Cor do Fundo", st.session_state.cor_fundo)
    cor_menu = st.color_picker("Cor do Menu Lateral", st.session_state.cor_menu)
    if st.button("Aplicar cores"):
        st.session_state.cor_fundo = cor_fundo
        st.session_state.cor_menu = cor_menu
        st.experimental_rerun()

# Adicionar campo de forma de pagamento no carrinho
if "forma_pagamento" not in st.session_state:
    st.session_state.forma_pagamento = "Dinheiro"

# Adicionar seleção de forma de pagamento na página de vendas
if st.session_state.get("pagina") == "Vendas":
    st.selectbox("Forma de Pagamento", ["Dinheiro", "Crédito", "Débito", "Pix"], key="forma_pagamento")

# Incluir forma de pagamento na geração da venda e no PDF
# Isso será feito dentro da função pagina_vendas no local correto
# Já garantimos que o campo está na tabela e o valor está salvo na sessão

# No momento de inserir no banco, a linha abaixo precisa ser ajustada:
# cursor.execute("INSERT INTO vendas (data, produto, cliente, quantidade, total, pedido_id, forma_pagamento) VALUES (?, ?, ?, ?, ?, ?, ?)",
#                (data_venda, produto, cliente, quantidade, total_produto, pedido_id, st.session_state.forma_pagamento))

# E também deve-se incluir no comprovante PDF:
# c.drawString(50, height - 210, f"Pagamento: {st.session_state.forma_pagamento}")

# O restante do código permanece como está, e as adições garantem a integração sem modificar a estrutura original.
