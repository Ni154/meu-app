import streamlit as st
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import pandas as pd
import plotly.express as px

# Inicializa banco de dados
conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# Criação das tabelas
cursor.execute("""
CREATE TABLE IF NOT EXISTS empresa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cnpj TEXT NOT NULL
)""")

# Adiciona a coluna ramo na tabela empresa se ainda não existir
cursor.execute("PRAGMA table_info(empresa)")
colunas = [col[1] for col in cursor.fetchall()]
if "ramo" not in colunas:
    cursor.execute("ALTER TABLE empresa ADD COLUMN ramo TEXT")
    conn.commit()

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

# Função para login
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
            st.stop()

# Tela inicial após login
st.sidebar.title("NS Sistemas")
menu = st.sidebar.radio("Menu", ["Início", "Empresa", "Clientes", "Produtos", "Vendas", "Relatórios"])

# Exibe dados da empresa e aplica tema conforme ramo
cursor.execute("SELECT nome, cnpj, ramo FROM empresa ORDER BY id DESC LIMIT 1")
dados_empresa = cursor.fetchone()

if dados_empresa:
    nome_emp, cnpj_emp, ramo_emp = dados_empresa
    st.markdown(f"### Empresa: {nome_emp}")
    st.markdown(f"**CNPJ:** {cnpj_emp}")
    st.markdown(f"**Ramo:** {ramo_emp}")

    # Aplicar tema CSS simples conforme ramo
    if ramo_emp == "Restaurante":
        st.markdown("""
        <style>
        .css-1d391kg {background-color: #FFF5E1 !important;}
        h3, h2, .css-1v3fvcr {color: #D35400 !important;}
        </style>
        """, unsafe_allow_html=True)
    elif ramo_emp == "Clínica":
        st.markdown("""
        <style>
        .css-1d391kg {background-color: #E6F0FF !important;}
        h3, h2, .css-1v3fvcr {color: #154360 !important;}
        </style>
        """, unsafe_allow_html=True)
    elif ramo_emp == "Mercado":
        st.markdown("""
        <style>
        .css-1d391kg {background-color: #E8F8F5 !important;}
        h3, h2, .css-1v3fvcr {color: #117A65 !important;}
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .css-1d391kg {background-color: #FFFFFF !important;}
        h3, h2, .css-1v3fvcr {color: #000000 !important;}
        </style>
        """, unsafe_allow_html=True)
else:
    st.warning("Nenhuma empresa cadastrada.")

# Cadastro da empresa
if menu == "Empresa":
    st.subheader("Cadastrar Empresa")
    nome_empresa = st.text_input("Nome da Empresa")
    cnpj_empresa = st.text_input("CNPJ")
    ramo = st.selectbox("Selecione o ramo da empresa", ["Restaurante", "Clínica", "Mercado", "Outro"])

    if st.button("Salvar Empresa"):
        if nome_empresa.strip() == "" or cnpj_empresa.strip() == "":
            st.error("Por favor, preencha nome e CNPJ.")
        else:
            cursor.execute("INSERT INTO empresa (nome, cnpj, ramo) VALUES (?, ?, ?)", (nome_empresa, cnpj_empresa, ramo))
            conn.commit()
            st.success("Empresa cadastrada!")
            st.experimental_rerun()

# Cadastro de clientes
elif menu == "Clientes":
    st.subheader("Cadastro de Cliente")
    nome = st.text_input("Nome")
    cpf = st.text_input("CPF")
    telefone = st.text_input("Telefone")
    if st.button("Cadastrar Cliente"):
        cursor.execute("INSERT INTO clientes (nome, cpf, telefone) VALUES (?, ?, ?)", (nome, cpf, telefone))
        conn.commit()
        st.success("Cliente cadastrado com sucesso")

# Cadastro de produtos
elif menu == "Produtos":
    st.subheader("Cadastro de Produtos")
    nome = st.text_input("Nome do Produto")
    preco = st.number_input("Preço", step=0.01)
    estoque = st.number_input("Estoque", step=1)
    categoria = st.text_input("Categoria")
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if st.button("Cadastrar Produto"):
        cursor.execute("INSERT INTO produtos (nome, preco, estoque, categoria, data) VALUES (?, ?, ?, ?, ?)",
                       (nome, preco, estoque, categoria, data))
        conn.commit()
        st.success("Produto cadastrado com sucesso")

    st.subheader("Produtos Cadastrados")
    produtos = cursor.execute("SELECT nome, preco, estoque, categoria FROM produtos").fetchall()
    st.dataframe(produtos)

# Tela de vendas
elif menu == "Vendas":
    st.subheader("Registrar Venda")
    produtos = [row[0] for row in cursor.execute("SELECT nome FROM produtos").fetchall()]
    clientes = [row[0] for row in cursor.execute("SELECT nome FROM clientes").fetchall()]

    if produtos and clientes:
        produto = st.selectbox("Produto", produtos)
        cliente = st.selectbox("Cliente", clientes)
        quantidade = st.number_input("Quantidade", min_value=1, step=1)

        if st.button("Finalizar Venda"):
            produto_info = cursor.execute("SELECT preco, estoque FROM produtos WHERE nome=?", (produto,)).fetchone()
            preco, estoque = produto_info
            if quantidade > estoque:
                st.warning("Estoque insuficiente")
            else:
                total = quantidade * preco
                data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute("INSERT INTO vendas (data, produto, cliente, quantidade, total) VALUES (?, ?, ?, ?, ?)",
                               (data_venda, produto, cliente, quantidade, total))
                cursor.execute("UPDATE produtos SET estoque=estoque-? WHERE nome=?", (quantidade, produto))
                conn.commit()

                buffer = io.BytesIO()
                c = canvas.Canvas(buffer)
                c.drawString(100, 800, "NS SISTEMAS - COMPROVANTE DE VENDA")
                c.drawString(100, 780, f"Data: {data_venda}")
                c.drawString(100, 760, f"Cliente: {cliente}")
                c.drawString(100, 740, f"Produto: {produto}")
                c.drawString(100, 720, f"Quantidade: {quantidade}")
                c.drawString(100, 700, f"Total: R$ {total:.2f}")
                c.save()

                st.download_button("Baixar Comprovante em PDF", buffer.getvalue(), file_name="comprovante.pdf")
                st.success("Venda registrada com sucesso")
    else:
        st.info("Cadastre produtos e clientes antes de vender")

# Relatórios com gráficos e exportação em PDF
elif menu == "Relatórios":
    st.subheader("Relatório de Vendas")
    data_inicio = st.date_input("Data inicial")
    data_fim = st.date_input("Data final")

    vendas = cursor.execute("SELECT data, produto, cliente, quantidade, total FROM vendas").fetchall()
    df = [v for v in vendas if data_inicio.strftime("%Y-%m-%d") <= v[0][:10] <= data_fim.strftime("%Y-%m-%d")]

    st.write("### Vendas no Período")
    st.dataframe(df)

    total = sum([v[4] for v in df])
    st.success(f"Total vendido no período: R$ {total:.2f}")

    # Gráfico de vendas
    df_vendas = pd.DataFrame(df, columns=["Data", "Produto", "Cliente", "Quantidade", "Total"])
    df_vendas["Data"] = pd.to_datetime(df_vendas["Data"])
    if not df_vendas.empty:
        grafico = px.bar(df_vendas, x="Data", y="Total", color="Produto", title="Vendas por Produto")
        st.plotly_chart(grafico)

        # Exportar PDF
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

        st.download_button("Baixar Relatório em PDF", buffer_pdf.getvalue(), file_name="relatorio_vendas.pdf")
