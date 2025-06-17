import streamlit as st
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io

# --------- Banco de Dados ----------
conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# Criar tabelas (se não existirem)
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL
)""")
conn.commit()

# Criar usuário padrão para primeiro acesso, se não existir
cursor.execute("SELECT * FROM usuarios WHERE usuario='admin'")
if cursor.fetchone() is None:
    cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ("admin", "1234"))
    conn.commit()

# --------- Temas ---------
temas = {
    "Restaurante": {
        "primaryColor": "#E63946",
        "backgroundColor": "#F1FAEE",
        "secondaryBackgroundColor": "#A8DADC",
        "textColor": "#1D3557",
        "font": "serif",
        "banner": "🍽️ Restaurante"
    },
    "Mercado": {
        "primaryColor": "#2A9D8F",
        "backgroundColor": "#E9F5F4",
        "secondaryBackgroundColor": "#264653",
        "textColor": "#264653",
        "font": "monospace",
        "banner": "🛒 Mercado"
    },
    "Clínica": {
        "primaryColor": "#457B9D",
        "backgroundColor": "#F0F4F8",
        "secondaryBackgroundColor": "#A9CCE3",
        "textColor": "#1B263B",
        "font": "sans-serif",
        "banner": "🏥 Clínica"
    },
    "Estética": {
        "primaryColor": "#DDA0DD",
        "backgroundColor": "#FFF0F5",
        "secondaryBackgroundColor": "#E6CCE6",
        "textColor": "#4B0082",
        "font": "cursive",
        "banner": "💄 Estética"
    }
}

# --------- Sessão e login ---------
if "logado" not in st.session_state:
    st.session_state.logado = False
if "tema" not in st.session_state:
    st.session_state.tema = "Restaurante"  # tema padrão

def aplicar_tema(tema_nome):
    tema = temas[tema_nome]
    st.markdown(f"""
        <style>
            .reportview-container {{
                background-color: {tema['backgroundColor']};
                color: {tema['textColor']};
                font-family: {tema['font']};
            }}
            .sidebar .sidebar-content {{
                background-color: {tema['secondaryBackgroundColor']};
                color: {tema['textColor']};
            }}
            .stButton>button {{
                background-color: {tema['primaryColor']};
                color: white;
                border-radius: 5px;
                height: 2.5em;
                width: 100%;
                font-weight: bold;
            }}
            .stSelectbox>div>div>div {{
                border: 2px solid {tema['primaryColor']} !important;
                border-radius: 6px;
            }}
            h1, h2, h3 {{
                color: {tema['primaryColor']};
            }}
        </style>
    """, unsafe_allow_html=True)

if not st.session_state.logado:
    st.title("NS Sistemas - Login")
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

# Após login
# Menu lateral fixo
st.sidebar.title("NS Sistemas")

# Seleção de tema no menu lateral
tema_selecionado = st.sidebar.selectbox("Escolha o tema", list(temas.keys()), index=list(temas.keys()).index(st.session_state.tema))
if tema_selecionado != st.session_state.tema:
    st.session_state.tema = tema_selecionado
    st.experimental_rerun()

aplicar_tema(st.session_state.tema)

st.sidebar.markdown(f"## {temas[st.session_state.tema]['banner']}")

menu = st.sidebar.radio("Menu", ["Vendas", "Clientes", "Produtos", "Relatórios", "Sair"])

# Função para deslogar
def logout():
    st.session_state.logado = False
    st.experimental_rerun()

if menu == "Sair":
    logout()

# Menu Vendas - tela inicial
elif menu == "Vendas":
    st.title("Registrar Venda")
    st.write(f"Tema atual: **{st.session_state.tema}**")
    # Aqui você coloca seu código para registrar venda
    st.info("Aqui você pode implementar o painel de vendas.")

elif menu == "Clientes":
    st.title("Clientes")
    st.info("Aqui você pode implementar o cadastro e listagem de clientes.")

elif menu == "Produtos":
    st.title("Produtos")
    st.info("Aqui você pode implementar o cadastro e listagem de produtos.")

elif menu == "Relatórios":
    st.title("Relatórios")
    st.info("Aqui você pode implementar os relatórios de vendas.")

