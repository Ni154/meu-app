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
if cursor.fetchone()[[0]] == 0:
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
    nome = st.text_input("Nome da Empresa")
    cnpj = st.text_input("CNPJ")
    if st.button("Salvar Empresa"):
        if nome and cnpj:
            cursor.execute("INSERT INTO clientes (nome, cpf, telefone, endereco) VALUES (?, ?, ?, ?)", (nome, cnpj, "", ""))
            conn.commit()
            st.success("Empresa cadastrada com sucesso")
        else:
            st.warning("Preencha todos os campos.")

def pagina_clientes():
    st.subheader("👥 Cadastro de Clientes")
    nome = st.text_input("Nome do Cliente")
    cpf = st.text_input("CPF")
    telefone = st.text_input("Telefone")
    endereco = st.text_area("Endereço")
    if st.button("Cadastrar Cliente"):
        if nome:
            cursor.execute("INSERT INTO clientes (nome, cpf, telefone, endereco) VALUES (?, ?, ?, ?)", (nome, cpf, telefone, endereco))
            conn.commit()
            st.success("Cliente cadastrado com sucesso")
        else:
            st.warning("Informe o nome do cliente.")

def pagina_produtos():
    st.subheader("🍟 Cadastro de Produtos")
    nome = st.text_input("Nome do Produto")
    preco = st.number_input("Preço", step=0.01)
    estoque = st.number_input("Estoque", step=1)
    unidade = st.selectbox("Unidade", ["Unidade", "Peso"])
    categoria = st.text_input("Categoria")
    if st.button("Cadastrar Produto"):
        if nome:
            data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO produtos (nome, preco, estoque, unidade, categoria, data) VALUES (?, ?, ?, ?, ?, ?)", (nome, preco, estoque, unidade, categoria, data))
            conn.commit()
            st.success("Produto cadastrado com sucesso")
        else:
            st.warning("Informe o nome do produto.")

def pagina_vendas():
    st.subheader("🧾 Registrar Venda")
    clientes = [row[0] for row in cursor.execute("SELECT nome FROM clientes").fetchall()]
    produtos = cursor.execute("SELECT nome, preco, estoque FROM produtos").fetchall()
    if clientes and produtos:
        cliente = st.selectbox("Cliente", clientes)
        produto_nome = st.selectbox("Produto", [p[0] for p in produtos])
        quantidade = st.number_input("Quantidade", min_value=1, step=1)
        produto_info = next(p for p in produtos if p[0] == produto_nome)
        preco_unit = produto_info[1]
        estoque = produto_info[2]
        total = preco_unit * quantidade
        st.write(f"Total: R$ {total:.2f}")
        if quantidade > estoque:
            st.warning("Estoque insuficiente.")
        if st.button("Finalizar Venda"):
            if quantidade <= estoque:
                pedido_id = str(uuid.uuid4())[:8]
                data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("INSERT INTO vendas (data, produto, cliente, quantidade, total, pedido_id) VALUES (?, ?, ?, ?, ?, ?)", (data, produto_nome, cliente, quantidade, total, pedido_id))
                cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE nome = ?", (quantidade, produto_nome))
                conn.commit()
                st.success("Venda registrada com sucesso!")
            else:
                st.error("Estoque insuficiente para completar a venda.")
    else:
        st.warning("Cadastre clientes e produtos primeiro.")

def pagina_cancelar_venda():
    st.subheader("❌ Cancelar Venda")
    vendas = cursor.execute("SELECT id, produto, cliente, quantidade, total FROM vendas WHERE status='Ativa'").fetchall()
    if vendas:
        venda_id = st.selectbox("Selecione a venda para cancelar", [f"ID {v[0]} - {v[1]} - {v[2]}" for v in vendas])
        if st.button("Cancelar Venda"):
            id_real = int(venda_id.split()[1])
            cursor.execute("UPDATE vendas SET status='Cancelada' WHERE id=?", (id_real,))
            conn.commit()
            st.success("Venda cancelada.")
    else:
        st.info("Nenhuma venda ativa encontrada.")

def pagina_relatorios():
    st.subheader("📊 Relatórios de Vendas e Estoque")
    df_vendas = pd.read_sql("SELECT * FROM vendas", conn)
    df_produtos = pd.read_sql("SELECT * FROM produtos", conn)
    st.write("### Relatório de Vendas")
    st.dataframe(df_vendas)
    st.write("### Gráfico de Vendas por Produto")
    if not df_vendas.empty:
        graf = px.bar(df_vendas, x="produto", y="total", color="cliente", title="Vendas por Produto")
        st.plotly_chart(graf)
    st.write("### Estoque Atual")
    st.dataframe(df_produtos[["nome", "estoque", "categoria"]])

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
