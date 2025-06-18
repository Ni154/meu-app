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
    pedido_id TEXT
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

def pagina_inicio():
    st.subheader("📊 Painel Administrativo")

    total_clientes = cursor.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    total_vendas = cursor.execute("SELECT SUM(total) FROM vendas WHERE status='Ativa'").fetchone()[0] or 0
    produtos = cursor.execute("SELECT nome, estoque FROM produtos").fetchall()
    produtos_negativos = [p[0] for p in produtos if p[1] <= 0]

    col1, col2 = st.columns(2)
    col1.metric("Total de Clientes", total_clientes)
    col2.metric("Total em Vendas", f"R$ {total_vendas:.2f}")

    if produtos_negativos:
        st.warning("⚠️ Produtos com estoque esgotado:")
        for p in produtos_negativos:
            st.write(f"- {p}")
    else:
        st.success("Todos os produtos estão com estoque disponível.")


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
    produtos_selecionados = st.multiselect("Produtos", [p[0] for p in produtos_info])
    quantidades = {}
    total = 0
    for prod in produtos_selecionados:
        prod_info = next(p for p in produtos_info if p[0] == prod)
        quantidade = st.number_input(f"Quantidade de {prod}", min_value=1, max_value=prod_info[2], step=1)
        quantidades[prod] = quantidade
        total += quantidade * prod_info[1]

    if st.button("Finalizar Venda"):
        data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pedido_id = datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4())[:6]
        for produto, quantidade in quantidades.items():
            preco_unit = next(p for p in produtos_info if p[0] == produto)[1]
            total_produto = preco_unit * quantidade
            cursor.execute("INSERT INTO vendas (data, produto, cliente, quantidade, total, pedido_id) VALUES (?, ?, ?, ?, ?, ?)", (data_venda, produto, cliente, quantidade, total_produto, pedido_id))
            cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE nome = ?", (quantidade, produto))
        conn.commit()

        st.success("Venda registrada com sucesso!")
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        c.drawString(100, 800, f"Comprovante - NS Lanches")
        c.drawString(100, 780, f"Data: {data_venda}")
        c.drawString(100, 760, f"Cliente: {cliente}")
        y = 740
        for produto, qtd in quantidades.items():
            preco_unit = next(p for p in produtos_info if p[0] == produto)[1]
            c.drawString(100, y, f"Produto: {produto} | Qtde: {qtd} | Unit: R$ {preco_unit:.2f}")
            y -= 20
        c.drawString(100, y, f"Total: R$ {total:.2f}")
        c.save()
        buffer.seek(0)
        st.download_button("📥 Baixar Comprovante PDF", buffer, file_name="comprovante.pdf")

def pagina_cancelar_venda():
    st.subheader("❌ Cancelar Venda")
    vendas = cursor.execute("SELECT pedido_id, cliente, data, SUM(total) FROM vendas WHERE status='Ativa' GROUP BY pedido_id").fetchall()
    if vendas:
        pedidos = [f"{v[0]} | {v[1]} | {v[2]} | R$ {v[3]:.2f}" for v in vendas]
        selecao = st.selectbox("Selecione uma venda para cancelar", pedidos)
        pedido_id = selecao.split("|")[0].strip()
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

if not st.session_state.logado:
    pagina_login()

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
