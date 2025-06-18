import streamlit as st
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import pandas as pd
import plotly.express as px
import uuid

# Conexão com banco de dados
conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# Criação das tabelas
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

# Estilo customizado para cores dinâmicas
st.set_page_config(layout="wide", page_title="NS Lanches")
st.markdown(f"""
    <style>
        .stApp {{ background-color: {st.session_state.cor_fundo}; }}
        .css-1d391kg {{ background-color: {st.session_state.cor_menu}; }}
    </style>
""", unsafe_allow_html=True)

# Páginas
def pagina_login():
    st.title("🍔 NS Lanches - Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    entrar = st.button("Entrar")
    
    if entrar:
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
        if cursor.fetchone():
            st.session_state.logado = True
            st.experimental_rerun()  # Recarrega a aplicação após login
        else:
            st.error("Usuário ou senha incorretos")

    if not st.session_state.logado:
        st.stop()  # Para de rodar o resto do app até que faça login


def pagina_inicio():
    st.subheader("🍔 Bem-vindo ao sistema de vendas NS Lanches")
    st.write("Utilize o menu lateral para navegar entre as funcionalidades.")

def pagina_empresa():
    st.subheader("🏢 Cadastro de Empresa")
    nome = st.text_input("Nome da Empresa")
    cnpj = st.text_input("CNPJ")
    if st.button("Salvar Empresa"):
        if nome and cnpj:
            cursor.execute("INSERT INTO empresa (nome, cnpj) VALUES (?, ?)", (nome, cnpj))
            conn.commit()
            st.success("Empresa cadastrada com sucesso")
        else:
            st.warning("Preencha todos os campos")

def pagina_clientes():
    st.subheader("👥 Cadastro de Clientes")
    nome = st.text_input("Nome")
    cpf = st.text_input("CPF")
    telefone = st.text_input("Telefone")
    endereco = st.text_area("Endereço")
    if st.button("Cadastrar Cliente"):
        if nome:
            cursor.execute("INSERT INTO clientes (nome, cpf, telefone, endereco) VALUES (?, ?, ?, ?)", (nome, cpf, telefone, endereco))
            conn.commit()
            st.success("Cliente cadastrado com sucesso")
        else:
            st.warning("Nome é obrigatório")

def pagina_produtos():
    st.subheader("🍟 Cadastro de Produtos")
    nome = st.text_input("Nome do Produto")
    preco = st.number_input("Preço", step=0.01)
    estoque = st.number_input("Estoque", step=1)
    unidade = st.selectbox("Unidade", ["Unidade", "Kg", "Litro"])
    categoria = st.text_input("Categoria")
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if st.button("Cadastrar Produto"):
        if nome:
            cursor.execute("INSERT INTO produtos (nome, preco, estoque, unidade, categoria, data) VALUES (?, ?, ?, ?, ?, ?)", (nome, preco, estoque, unidade, categoria, data))
            conn.commit()
            st.success("Produto cadastrado com sucesso")
        else:
            st.warning("Nome do produto é obrigatório")

def pagina_vendas():
    st.subheader("🧾 Registrar Venda")
    clientes = [c[0] for c in cursor.execute("SELECT nome FROM clientes").fetchall()]
    produtos_info = cursor.execute("SELECT nome, preco, estoque FROM produtos WHERE estoque > 0").fetchall()
    if not clientes or not produtos_info:
        st.info("Cadastre clientes e produtos antes de registrar vendas")
        return

    cliente = st.selectbox("Cliente", clientes)
    produto = st.selectbox("Produto", [p[0] for p in produtos_info])
    quantidade = st.number_input("Quantidade", min_value=1, step=1)

    produto_sel = next(p for p in produtos_info if p[0] == produto)
    preco = produto_sel[1]
    estoque = produto_sel[2]

    if quantidade > estoque:
        st.warning("Quantidade maior que o estoque disponível")
        return

    if st.button("Finalizar Venda"):
        total = preco * quantidade
        data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pedido_id = datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4())[:6]

        cursor.execute("INSERT INTO vendas (data, produto, cliente, quantidade, total, pedido_id) VALUES (?, ?, ?, ?, ?, ?)",
                       (data_venda, produto, cliente, quantidade, total, pedido_id))
        cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE nome = ?", (quantidade, produto))
        conn.commit()

        st.success("Venda registrada com sucesso!")

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        c.drawString(100, 800, f"Comprovante - NS Lanches")
        c.drawString(100, 780, f"Data: {data_venda}")
        c.drawString(100, 760, f"Cliente: {cliente}")
        c.drawString(100, 740, f"Produto: {produto}")
        c.drawString(100, 720, f"Quantidade: {quantidade}")
        c.drawString(100, 700, f"Total: R$ {total:.2f}")
        c.save()
        buffer.seek(0)
        st.download_button("📥 Baixar Comprovante PDF", buffer, file_name="comprovante.pdf")

def pagina_cancelar_venda():
    st.subheader("❌ Cancelar Venda")
    pedidos = cursor.execute("SELECT DISTINCT pedido_id FROM vendas WHERE status='Ativa'").fetchall()
    if pedidos:
        pedido_id = st.selectbox("Selecione um Pedido", [p[0] for p in pedidos])
        if st.button("Cancelar Pedido"):
            cursor.execute("UPDATE vendas SET status='Cancelada' WHERE pedido_id=?", (pedido_id,))
            conn.commit()
            st.success("Pedido cancelado com sucesso")
    else:
        st.info("Nenhum pedido ativo para cancelar")

def pagina_relatorios():
    st.subheader("📊 Relatórios de Vendas")
    vendas = cursor.execute("SELECT data, produto, cliente, quantidade, total FROM vendas WHERE status='Ativa'").fetchall()
    if not vendas:
        st.info("Nenhuma venda registrada")
        return

    df = pd.DataFrame(vendas, columns=["Data", "Produto", "Cliente", "Quantidade", "Total"])
    st.dataframe(df)

    st.plotly_chart(px.bar(df, x="Produto", y="Total", title="Vendas por Produto"))
    st.plotly_chart(px.bar(df, x="Cliente", y="Total", title="Vendas por Cliente"))

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.drawString(100, 800, "Relatório de Vendas")
    y = 780
    for index, row in df.iterrows():
        pdf.drawString(100, y, f"{row['Data']} | {row['Cliente']} | {row['Produto']} | Qtde: {row['Quantidade']} | R$ {row['Total']:.2f}")
        y -= 20
        if y < 50:
            pdf.showPage()
            y = 800
    pdf.save()
    buffer.seek(0)
    st.download_button("📥 Baixar Relatório PDF", buffer, file_name="relatorio_vendas.pdf")

# NOVO: Painel Administrativo
def pagina_admin():
    st.subheader("📊 Painel Administrativo")
    
    total_vendas = cursor.execute("SELECT SUM(total) FROM vendas WHERE status='Ativa'").fetchone()[0] or 0
    total_clientes = cursor.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    total_produtos = cursor.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    
    st.metric("💰 Total Vendido", f"R$ {total_vendas:.2f}")
    st.metric("👥 Clientes Cadastrados", total_clientes)
    st.metric("📦 Produtos Cadastrados", total_produtos)

    st.markdown("### ⚠️ Produtos com Estoque Baixo (≤ 5 unidades)")
    estoque_baixo = pd.read_sql("SELECT nome, estoque FROM produtos WHERE estoque <= 5", conn)
    if not estoque_baixo.empty:
        st.dataframe(estoque_baixo)
    else:
        st.write("Nenhum produto com estoque baixo.")

# Login
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
    if st.button("Painel Admin"):
        st.session_state.pagina = "Admin"

# Navegação entre páginas
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
elif pagina == "Admin":
    pagina_admin()
