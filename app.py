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

# Configura tema inicial
if "tema" not in st.session_state:
    st.session_state.tema = {
        "cor_botao": "blue",
        "estilo_botao": "filled"
    }

# Estilos de botão
def botao(texto, chave):
    cor = st.session_state.tema["cor_botao"]
    estilo = st.session_state.tema["estilo_botao"]
    estilo_css = f"background-color: {cor}; color: white; border: none; border-radius: 5px; padding: 10px; width: 100%;"
    if estilo == "outlined":
        estilo_css = f"color: {cor}; border: 2px solid {cor}; border-radius: 5px; padding: 10px; width: 100%; background-color: white"
    return st.button(texto, key=chave, help=texto, use_container_width=True)

# Inicializa banco de dados
conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# Cria tabelas
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
cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT,
    telefone TEXT
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

# Usuário padrão
cursor.execute("SELECT COUNT(*) FROM usuarios")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ("admin", "1234"))
    conn.commit()

# Login
if "logado" not in st.session_state:
    st.session_state.logado = False

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

# Interface após login
else:
    st.sidebar.image("logo.png") if os.path.exists("logo.png") else st.sidebar.write("[Logo não carregada]")
    st.sidebar.title("NS Sistemas")
    st.sidebar.subheader("Menu")
    botoes = ["Início", "Empresa", "Clientes", "Produtos", "Vendas", "Cancelar Venda", "Relatórios", "Configurações"]
    menu = None
    for i, nome in enumerate(botoes):
        if botao(nome, f"btn_{i}"):
            st.session_state.menu = nome
            st.rerun()

    menu = st.session_state.get("menu", "Início")

    if menu == "Configurações":
        st.subheader("Configurações de Tema")
        cor = st.color_picker("Escolha a cor dos botões", st.session_state.tema["cor_botao"])
        estilo = st.selectbox("Estilo do botão", ["filled", "outlined"], index=["filled", "outlined"].index(st.session_state.tema["estilo_botao"]))
        st.session_state.tema["cor_botao"] = cor
        st.session_state.tema["estilo_botao"] = estilo

        st.subheader("Importar logo")
        logo = st.file_uploader("Selecione a imagem da logo", type=["png", "jpg", "jpeg"])
        if logo:
            with open("logo.png", "wb") as f:
                f.write(logo.read())
            st.success("Logo salva com sucesso. Recarregue a página para visualizar.")

    else:
        st.write(f"### Tela selecionada: {menu}")
        # Aqui você pode adicionar o conteúdo correspondente a cada menu
        # como o já feito anteriormente no seu sistema para Empresa, Clientes etc.
