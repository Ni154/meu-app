# sistema_vendas_streamlit.py
import streamlit as st
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io
import pandas as pd
import plotly.express as px

# Conexão com o banco
conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# Estilo dos botões
COR_PADRAO = {
    "laranja": "#FFA500",
    "azul": "#007BFF",
    "verde": "#28a745",
    "vermelho": "#dc3545"
}

def aplicar_tema():
    cor = st.session_state.get("tema", "laranja")
    css = f"""
    <style>
    .stButton > button {{
        background-color: {COR_PADRAO.get(cor, '#FFA500')};
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.6em 1.5em;
        border: none;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def criar_tabelas():
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
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", ("admin", "1234"))

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cpf TEXT,
        telefone TEXT,
        endereco TEXT
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

def login():
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

def menu_lateral():
    with st.sidebar:
        st.title("NS Sistemas")
        st.session_state.logo = st.file_uploader("Logo da empresa", type=["png", "jpg", "jpeg"])
        st.session_state.tema = st.selectbox("Tema do botão", ["laranja", "azul", "verde", "vermelho"])
        if st.button("Início"): st.session_state.pagina = "Inicio"
        if st.button("Empresa"): st.session_state.pagina = "Empresa"
        if st.button("Clientes"): st.session_state.pagina = "Clientes"
        if st.button("Produtos"): st.session_state.pagina = "Produtos"
        if st.button("Vendas"): st.session_state.pagina = "Vendas"
        if st.button("Relatórios"): st.session_state.pagina = "Relatórios"

def pagina_empresa():
    st.subheader("Cadastrar Empresa")
    nome = st.text_input("Nome da Empresa")
    cnpj = st.text_input("CNPJ")
    if st.button("Salvar Empresa"):
        if nome and cnpj:
            cursor.execute("INSERT INTO empresa (nome, cnpj) VALUES (?, ?)", (nome, cnpj))
            conn.commit()
            st.success("Empresa cadastrada!")

    cursor.execute("SELECT nome, cnpj FROM empresa ORDER BY id DESC LIMIT 1")
    dados = cursor.fetchone()
    if dados:
        st.markdown(f"### Empresa: {dados[0]}  ")
        st.markdown(f"**CNPJ:** {dados[1]}")

def pagina_clientes():
    st.subheader("Cadastro de Cliente")
    nome = st.text_input("Nome")
    cpf = st.text_input("CPF")
    telefone = st.text_input("Telefone")
    endereco = st.text_area("Endereço")
    if st.button("Cadastrar Cliente"):
        if nome:
            cursor.execute("INSERT INTO clientes (nome, cpf, telefone, endereco) VALUES (?, ?, ?, ?)", (nome, cpf, telefone, endereco))
            conn.commit()
            st.success("Cliente cadastrado!")


def pagina_produtos():
    st.subheader("Cadastro de Produtos")
    nome = st.text_input("Nome do Produto")
    preco = st.number_input("Preço", step=0.01)
    estoque = st.number_input("Estoque", step=1)
    unidade = st.selectbox("Unidade", ["Unidade", "Peso"])
    categoria = st.text_input("Categoria")
    if st.button("Cadastrar Produto"):
        if nome:
            data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO produtos (nome, preco, estoque, unidade, categoria, data) VALUES (?, ?, ?, ?, ?, ?)",
                           (nome, preco, estoque, unidade, categoria, data))
            conn.commit()
            st.success("Produto cadastrado!")

    produtos_df = pd.read_sql("SELECT id, nome, preco, estoque, categoria FROM produtos", conn)
    for _, row in produtos_df.iterrows():
        st.write(f"**{row['nome']}** | Preço: R$ {row['preco']} | Estoque: {row['estoque']} | Categoria: {row['categoria']}")
        if st.button(f"Excluir {row['nome']}", key=row['id']):
            cursor.execute("DELETE FROM produtos WHERE id=?", (row['id'],))
            conn.commit()
            st.success("Produto excluído!")
            st.experimental_rerun()

def pagina_vendas():
    st.subheader("Registrar Venda")
    produtos = [r[0] for r in cursor.execute("SELECT nome FROM produtos").fetchall()]
    clientes = [r[0] for r in cursor.execute("SELECT nome FROM clientes").fetchall()]
    if produtos and clientes:
        produto = st.selectbox("Produto", produtos)
        produto_info = cursor.execute("SELECT preco, estoque FROM produtos WHERE nome=?", (produto,)).fetchone()

        cliente = st.selectbox("Cliente", clientes)
        cliente_info = None
        if cliente:
            try:
                cliente_info = cursor.execute("SELECT telefone, endereco FROM clientes WHERE nome=?", (cliente,)).fetchone()
            except Exception as e:
                st.error(f"Erro ao buscar cliente: {e}")

        quantidade = st.number_input("Quantidade", min_value=1)
        pagamento = st.selectbox("Forma de Pagamento", ["Dinheiro", "Cartão", "PIX"])

        if st.button("Finalizar Venda"):
            if produto_info and cliente_info:
                preco, estoque = produto_info
                if quantidade > estoque:
                    st.warning("Estoque insuficiente")
                else:
                    total = preco * quantidade
                    data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("INSERT INTO vendas (data, produto, cliente, quantidade, total) VALUES (?, ?, ?, ?, ?)",
                                   (data_venda, produto, cliente, quantidade, total))
                    cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE nome=?", (quantidade, produto))
                    conn.commit()

                    buffer = io.BytesIO()
                    c = canvas.Canvas(buffer)
                    c.drawString(100, 800, "NS SISTEMAS - COMPROVANTE DE VENDA")
                    c.drawString(100, 780, f"Data: {data_venda}")
                    c.drawString(100, 760, f"Cliente: {cliente}")
                    c.drawString(100, 740, f"Produto: {produto}")
                    c.drawString(100, 720, f"Quantidade: {quantidade}")
                    c.drawString(100, 700, f"Forma de Pagamento: {pagamento}")
                    c.drawString(100, 680, f"Total: R$ {total:.2f}")
                    c.save()

                    st.download_button("Baixar Comprovante", buffer.getvalue(), file_name="comprovante.pdf")
                    st.success("Venda registrada com sucesso")
    else:
        st.info("Cadastre produtos e clientes antes de realizar vendas")

def pagina_relatorios():
    st.subheader("Relatório de Vendas")
    data_inicio = st.date_input("Data Início")
    data_fim = st.date_input("Data Fim")

    vendas = cursor.execute("SELECT data, produto, cliente, quantidade, total FROM vendas").fetchall()
    df = pd.DataFrame([v for v in vendas if data_inicio.strftime("%Y-%m-%d") <= v[0][:10] <= data_fim.strftime("%Y-%m-%d")],
                      columns=["Data", "Produto", "Cliente", "Quantidade", "Total"])

    st.dataframe(df)
    total = df["Total"].sum()
    st.success(f"Total no período: R$ {total:.2f}")

    if not df.empty:
        grafico = px.bar(df, x="Data", y="Total", color="Produto", title="Vendas por Produto")
        st.plotly_chart(grafico)

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        pdf.drawString(100, 800, "Relatório de Vendas")
        pdf.drawString(100, 780, f"Período: {data_inicio} a {data_fim}")
        y = 760
        for _, row in df.iterrows():
            pdf.drawString(100, y, f"{row['Data']} - {row['Produto']} - {row['Cliente']} - Qtde: {row['Quantidade']} - R$ {row['Total']:.2f}")
            y -= 20
            if y < 50:
                pdf.showPage()
                y = 800
        pdf.drawString(100, y, f"Total: R$ {total:.2f}")
        pdf.save()

        st.download_button("Baixar Relatório PDF", buffer.getvalue(), file_name="relatorio.pdf")

# Execução principal
criar_tabelas()
aplicar_tema()

if "logado" not in st.session_state:
    st.session_state.logado = False
if "pagina" not in st.session_state:
    st.session_state.pagina = "Inicio"

if not st.session_state.logado:
    login()
else:
    menu_lateral()
    pagina = st.session_state.pagina
    if pagina == "Empresa": pagina_empresa()
    elif pagina == "Clientes": pagina_clientes()
    elif pagina == "Produtos": pagina_produtos()
    elif pagina == "Vendas": pagina_vendas()
    elif pagina == "Relatórios": pagina_relatorios()
