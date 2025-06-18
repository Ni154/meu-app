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
conn.commit()

# Cria um usuário padrão se não existir
cursor.execute("SELECT COUNT(*) FROM usuarios")
if cursor.fetchone()[0] == 0:
    cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ("admin", "1234"))
    conn.commit()

# Funções de páginas
def pagina_inicio():
    st.subheader("🍔 Bem-vindo ao sistema de vendas NS Lanches")
    st.write("Utilize o menu lateral para navegar entre as funcionalidades.")

def pagina_empresa():
    st.subheader("🏢 Cadastrar Empresa")
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
    st.subheader("👥 Cadastro de Cliente")
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
    st.subheader("🍟 Cadastro de Produtos")
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

def pagina_vendas():
    st.subheader("🧾 Registrar Venda")
    produtos = [row[0] for row in cursor.execute("SELECT nome FROM produtos").fetchall()]
    clientes = [row[0] for row in cursor.execute("SELECT nome FROM clientes").fetchall()]
    formas_pagamento = ["Dinheiro", "Cartão", "PIX"]

    if produtos and clientes:
        produto = st.selectbox("Produto", produtos)
        produto_info = cursor.execute("SELECT preco, estoque, unidade, categoria FROM produtos WHERE nome=?", (produto,)).fetchone()
        st.write(f"**Preço:** R$ {produto_info[0]} | **Estoque:** {produto_info[1]} | **Unidade:** {produto_info[2]} | **Categoria:** {produto_info[3]}")

        cliente = st.selectbox("Cliente", clientes)
        cliente_info = cursor.execute("SELECT telefone, endereco FROM clientes WHERE nome=?", (cliente,)).fetchone()
        st.write(f"**Telefone:** {cliente_info[0]} | **Endereço:** {cliente_info[1]}")

        forma_pagamento = st.selectbox("Forma de Pagamento", formas_pagamento)
        quantidade = st.number_input("Quantidade", min_value=1, step=1)

        if st.button("Finalizar Venda"):
            preco, estoque = produto_info[0], produto_info[1]
            if quantidade > estoque:
                st.warning("Estoque insuficiente")
            else:
                total = quantidade * preco
                data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                try:
                    cursor.execute("INSERT INTO vendas (data, produto, cliente, quantidade, total) VALUES (?, ?, ?, ?, ?)",
                        (data_venda, produto, cliente, quantidade, total))
                    cursor.execute("UPDATE produtos SET estoque=estoque-? WHERE nome=?", (quantidade, produto))
                    conn.commit()

                    buffer = io.BytesIO()
                    c = canvas.Canvas(buffer)
                    c.drawString(100, 800, "NS LANCHES - COMPROVANTE DE VENDA")
                    c.drawString(100, 780, f"Data: {data_venda}")
                    c.drawString(100, 760, f"Cliente: {cliente}")
                    c.drawString(100, 740, f"Endereço: {cliente_info[1]}")
                    c.drawString(100, 720, f"Telefone: {cliente_info[0]}")
                    c.drawString(100, 700, f"Produto: {produto}")
                    c.drawString(100, 680, f"Quantidade: {quantidade}")
                    c.drawString(100, 660, f"Forma de Pagamento: {forma_pagamento}")
                    c.drawString(100, 640, f"Total: R$ {total:.2f}")
                    c.save()

                    st.download_button("📥 Baixar Comprovante em PDF", buffer.getvalue(), file_name="comprovante.pdf")
                    st.success("Venda registrada com sucesso")
                except Exception as e:
                    st.error(f"Erro ao registrar venda: {e}")
    else:
        st.info("Cadastre produtos e clientes antes de vender")

def pagina_relatorios():
    st.subheader("📊 Relatórios")
    opcao = st.radio("Escolha o tipo de relatório:", ["Relatório de Vendas", "Relatório de Estoque"])

    if opcao == "Relatório de Vendas":
        data_inicio = st.date_input("Data inicial")
        data_fim = st.date_input("Data final")
        vendas = cursor.execute("SELECT data, produto, cliente, quantidade, total FROM vendas").fetchall()
        df = [v for v in vendas if data_inicio.strftime("%Y-%m-%d") <= v[0][:10] <= data_fim.strftime("%Y-%m-%d")]

        st.write("### Vendas no Período")
        df_vendas = pd.DataFrame(df, columns=["Data", "Produto", "Cliente", "Quantidade", "Total"])
        st.dataframe(df_vendas)

        total = sum([v[4] for v in df])
        st.success(f"Total vendido no período: R$ {total:.2f}")

        if not df_vendas.empty:
            df_vendas["Data"] = pd.to_datetime(df_vendas["Data"])
            grafico = px.bar(df_vendas, x="Data", y="Total", color="Produto", title="Vendas por Produto")
            st.plotly_chart(grafico)

            buffer_pdf = io.BytesIO()
            pdf = canvas.Canvas(buffer_pdf, pagesize=A4)
            pdf.drawString(100, 800, "Relatório de Vendas")
            pdf.drawString(100, 780, f"Período: {data_inicio} até {data_fim}")
            y = 760
            for v in df:
                linha = f"{v[0]} - {v[1]} - {v[2]} - Qtde: {v[3]} - R$ {v[4]:.2f}"
                pdf.drawString(100, y, linha)
                y -= 20
                if y < 50:
                    pdf.showPage()
                    y = 800
            pdf.drawString(100, y, f"Total vendido: R$ {total:.2f}")
            pdf.save()

            st.download_button("📥 Baixar Relatório em PDF", buffer_pdf.getvalue(), file_name="relatorio_vendas.pdf")

    elif opcao == "Relatório de Estoque":
        produtos_df = pd.read_sql("SELECT nome, estoque, preco, categoria FROM produtos", conn)
        st.dataframe(produtos_df)
        st.plotly_chart(px.bar(produtos_df, x="nome", y="estoque", color="categoria", title="Estoque Atual por Produto"))

# Configurações iniciais da página
st.set_page_config(layout="wide", page_title="NS Lanches")
st.markdown(
    """
    <style>
    .stApp {
        background-image: url('https://cdn.pixabay.com/photo/2016/11/29/04/17/burger-1869658_960_720.jpg');
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    .stButton>button {
        background-color: #FF8C00;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 16px;
        margin-bottom: 10px;
    }
    .stButton>button:hover {
        background-color: #e67e00;
    }
    .sidebar .block-container {
        background-color: rgba(255, 255, 255, 0.8);
        padding: 10px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if "logado" not in st.session_state:
    st.session_state.logado = False
if not st.session_state.logado:
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

if "pagina" not in st.session_state:
    st.session_state.pagina = "Início"
if "logo" not in st.session_state:
    st.session_state.logo = None

# Sidebar
with st.sidebar:
    st.title("🍟 NS Lanches")
    st.session_state.logo = st.file_uploader("Logo da empresa", type=["png", "jpg", "jpeg"])
    if st.session_state.logo:
        st.image(st.session_state.logo, width=200)
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

# Exibir página
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
