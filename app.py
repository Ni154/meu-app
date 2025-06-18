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

# Criação das tabelas se não existirem
cursor.execute("""
CREATE TABLE IF NOT EXISTS empresa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cnpj TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL,
    senha TEXT NOT NULL
)
""")

# Cria usuário padrão
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
    total REAL
)
""")

conn.commit()

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

def gerar_comprovante_pdf(data, cliente, produto, quantidade, forma_pagamento, total):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.drawString(100, 800, "NS SISTEMAS - COMPROVANTE DE VENDA")
    c.drawString(100, 780, f"Data: {data}")
    c.drawString(100, 760, f"Cliente: {cliente}")
    c.drawString(100, 740, f"Produto: {produto}")
    c.drawString(100, 720, f"Quantidade: {quantidade}")
    c.drawString(100, 700, f"Forma de Pagamento: {forma_pagamento}")
    c.drawString(100, 680, f"Total: R$ {total:.2f}")
    c.save()
    return buffer

def pagina_vendas():
    st.subheader("Registrar Venda")
    produtos = [row[0] for row in cursor.execute("SELECT nome FROM produtos").fetchall()]
    clientes = [row[0] for row in cursor.execute("SELECT nome FROM clientes").fetchall()]
    formas_pagamento = ["Dinheiro", "Cartão", "PIX"]

    if produtos and clientes:
        produto = st.selectbox("Produto", produtos)
        produto_info = cursor.execute("SELECT preco, estoque FROM produtos WHERE nome=?", (produto,)).fetchone()
        st.write(f"Preço: R$ {produto_info[0]:.2f} | Estoque: {produto_info[1]}")

        cliente = st.selectbox("Cliente", clientes)
        forma_pagamento = st.selectbox("Forma de Pagamento", formas_pagamento)
        quantidade = st.number_input("Quantidade", min_value=1, step=1)

        if st.button("Finalizar Venda"):
            preco, estoque = produto_info
            if quantidade > estoque:
                st.warning("Estoque insuficiente")
            else:
                total = quantidade * preco
                data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    cursor.execute("INSERT INTO vendas (data, produto, cliente, quantidade, total) VALUES (?, ?, ?, ?, ?)",
                        (data_venda, produto, cliente, quantidade, total))
                    cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE nome = ?", (quantidade, produto))
                    conn.commit()
                    pdf_buffer = gerar_comprovante_pdf(data_venda, cliente, produto, quantidade, forma_pagamento, total)
                    st.download_button("Baixar Comprovante em PDF", pdf_buffer.getvalue(), file_name="comprovante.pdf")
                    st.success("Venda registrada com sucesso")
                except Exception as e:
                    st.error(f"Erro ao registrar venda: {e}")
    else:
        st.info("Cadastre produtos e clientes primeiro")

def pagina_relatorios():
    st.subheader("Relatórios")
    opcao = st.radio("Escolha o tipo de relatório", ["Relatório de Vendas", "Relatório de Estoque"])

    if opcao == "Relatório de Vendas":
        data_inicio = st.date_input("Data inicial")
        data_fim = st.date_input("Data final")
        cliente_filtro = st.text_input("Filtrar por cliente (opcional)")
        produto_filtro = st.text_input("Filtrar por produto (opcional)")

        query = "SELECT data, produto, cliente, quantidade, total FROM vendas"
        df_vendas = pd.read_sql(query, conn)
        df_vendas["Data"] = pd.to_datetime(df_vendas["data"])
        df_vendas = df_vendas[(df_vendas["Data"] >= pd.to_datetime(data_inicio)) & (df_vendas["Data"] <= pd.to_datetime(data_fim))]

        if cliente_filtro:
            df_vendas = df_vendas[df_vendas["cliente"].str.contains(cliente_filtro, case=False)]
        if produto_filtro:
            df_vendas = df_vendas[df_vendas["produto"].str.contains(produto_filtro, case=False)]

        st.dataframe(df_vendas)
        total = df_vendas["total"].sum()
        st.success(f"Total vendido no período: R$ {total:.2f}")

        if not df_vendas.empty:
            st.plotly_chart(px.bar(df_vendas, x="Data", y="total", color="produto", title="Vendas por Produto"))

        if st.button("Exportar Relatório em PDF"):
            pdf_buffer = io.BytesIO()
            pdf = canvas.Canvas(pdf_buffer, pagesize=A4)
            pdf.drawString(100, 800, "Relatório de Vendas")
            y = 780
            for index, row in df_vendas.iterrows():
                linha = f"{row['Data'].strftime('%Y-%m-%d')} - {row['produto']} - {row['cliente']} - Qtde: {row['quantidade']} - R$ {row['total']:.2f}"
                pdf.drawString(100, y, linha)
                y -= 20
                if y < 50:
                    pdf.showPage()
                    y = 800
            pdf.drawString(100, y, f"Total vendido: R$ {total:.2f}")
            pdf.save()
            st.download_button("Baixar PDF", pdf_buffer.getvalue(), file_name="relatorio_vendas.pdf")

    elif opcao == "Relatório de Estoque":
        produtos_df = pd.read_sql("SELECT nome, estoque, preco, categoria FROM produtos", conn)
        st.dataframe(produtos_df)
        st.plotly_chart(px.bar(produtos_df, x="nome", y="estoque", color="categoria", title="Estoque Atual"))

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
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha incorretos")
else:
    st.set_page_config(layout="wide")
    st.markdown("""
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
        .sidebar .block-container {
            background-image: url('https://img.freepik.com/vetores-gratis/fundo-de-grade-azul-gradiente_23-2149333607.jpg');
            background-size: cover;
        }
        </style>
    """, unsafe_allow_html=True)

    if "pagina" not in st.session_state:
        st.session_state.pagina = "Início"
    if "logo" not in st.session_state:
        st.session_state.logo = None

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
        if st.button("Relatórios"):
            st.session_state.pagina = "Relatórios"

    pagina = st.session_state.pagina
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
    elif pagina == "Relatórios":
        pagina_relatorios()
