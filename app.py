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
        st.rerun()

def pagina_login():
    st.title("🍔 NS Lanches - Login")
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

    # Inicializa o carrinho na sessão
    if "carrinho" not in st.session_state:
        st.session_state.carrinho = {}

    # Seleciona produto e quantidade para adicionar ao carrinho
    col1, col2 = st.columns([3,1])
    with col1:
        produto_selecionado = st.selectbox("Selecione o Produto para adicionar", [p[0] for p in produtos_info])
    with col2:
        estoque_prod = next(p[2] for p in produtos_info if p[0] == produto_selecionado)
        quantidade = st.number_input("Quantidade", min_value=1, max_value=estoque_prod, step=1, key="qtde_add")

    if st.button("Adicionar ao Carrinho"):
        if produto_selecionado in st.session_state.carrinho:
            # Soma a quantidade se já tiver no carrinho
            nova_qtde = st.session_state.carrinho[produto_selecionado] + quantidade
            if nova_qtde <= estoque_prod:
                st.session_state.carrinho[produto_selecionado] = nova_qtde
            else:
                st.warning(f"Estoque insuficiente para adicionar {quantidade} unidades adicionais.")
        else:
            st.session_state.carrinho[produto_selecionado] = quantidade
        st.success(f"{quantidade} x {produto_selecionado} adicionado(s) ao carrinho.")

    # Exibe itens no carrinho
    st.markdown("### Carrinho de Compras")
    if st.session_state.carrinho:
        total = 0
        for prod, qtde in st.session_state.carrinho.items():
            preco_unit = next(p[1] for p in produtos_info if p[0] == prod)
            subtotal = preco_unit * qtde
            total += subtotal
            st.write(f"{prod} - Quantidade: {qtde} - Subtotal: R$ {subtotal:.2f}")

        st.markdown(f"**Total da Venda: R$ {total:.2f}**")

        if st.button("Finalizar Venda"):
            data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pedido_id = datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4())[:6]

            # Busca dados completos do cliente
            cursor.execute("SELECT nome, cpf, telefone, endereco FROM clientes WHERE nome=?", (cliente,))
            dados_cliente = cursor.fetchone()
            nome_cliente = dados_cliente[0]
            cpf_cliente = dados_cliente[1]
            telefone_cliente = dados_cliente[2]
            endereco_cliente = dados_cliente[3]

            for produto, quantidade in st.session_state.carrinho.items():
                preco_unit = next(p[1] for p in produtos_info if p[0] == produto)
                total_produto = preco_unit * quantidade
                cursor.execute("INSERT INTO vendas (data, produto, cliente, quantidade, total, pedido_id) VALUES (?, ?, ?, ?, ?, ?)",
                               (data_venda, produto, cliente, quantidade, total_produto, pedido_id))
                cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE nome = ?", (quantidade, produto))
            conn.commit()

            # Criar comprovante PDF melhorado
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4

            c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(width / 2, height - 50, "Comprovante de Venda - NS Lanches")

            c.setLineWidth(1)
            c.line(50, height - 60, width - 50, height - 60)

            c.setFont("Helvetica", 12)
            c.drawString(50, height - 90, f"Data: {data_venda}")
            c.drawString(50, height - 110, f"Cliente: {nome_cliente}")
            c.drawString(50, height - 130, f"CPF: {cpf_cliente}")
            c.drawString(50, height - 150, f"Telefone: {telefone_cliente}")
            c.drawString(50, height - 170, f"Endereço: {endereco_cliente}")
            c.drawString(50, height - 190, f"Pedido ID: {pedido_id}")

            # Cabeçalho da tabela
            y = height - 220
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Produto")
            c.drawString(280, y, "Qtde")
            c.drawString(350, y, "Unitário (R$)")
            c.drawString(460, y, "Subtotal (R$)")

            c.setLineWidth(0.5)
            c.line(50, y - 5, width - 50, y - 5)

            # Itens
            c.setFont("Helvetica", 12)
            y -= 30
            total = 0
            for produto, qtde in st.session_state.carrinho.items():
                preco_unit = next(p[1] for p in produtos_info if p[0] == produto)
                subtotal = preco_unit * qtde
                total += subtotal

                c.drawString(50, y, produto)
                c.drawRightString(320, y, str(qtde))
                c.drawRightString(420, y, f"{preco_unit:.2f}")
                c.drawRightString(520, y, f"{subtotal:.2f}")
                y -= 20
                if y < 50:
                    c.showPage()
                    y = height - 50

            # Linha separadora antes do total
            c.line(350, y, 520, y)
            y -= 20

            c.setFont("Helvetica-Bold", 14)
            c.drawString(350, y, "Total:")
            c.drawRightString(520, y, f"R$ {total:.2f}")

            c.save()
            buffer.seek(0)

            st.success("Venda registrada com sucesso!")
            st.download_button("📥 Baixar Comprovante PDF", buffer, file_name="comprovante.pdf")

            # Limpa o carrinho após finalizar
            st.session_state.carrinho = {}

    else:
        st.info("Carrinho vazio. Adicione produtos para iniciar a venda.")

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

    # Filtros de data
    data_inicial = st.date_input("Data Inicial", value=datetime.now().date())
    data_final = st.date_input("Data Final", value=datetime.now().date())

    if data_inicial > data_final:
        st.error("A Data Inicial não pode ser maior que a Data Final.")
        return

    # Buscar vendas no período filtrado
    cursor.execute("""
        SELECT data, produto, cliente, quantidade, total FROM vendas
        WHERE status='Ativa' AND date(data) BETWEEN ? AND ?
    """, (data_inicial.strftime("%Y-%m-%d"), data_final.strftime("%Y-%m-%d")))
    vendas = cursor.fetchall()

    if not vendas:
        st.info("Nenhuma venda registrada neste período.")
        return

    df = pd.DataFrame(vendas, columns=["Data", "Produto", "Cliente", "Quantidade", "Total"])

    st.dataframe(df)

    st.plotly_chart(px.bar(df, x="Produto", y="Total", title="Vendas por Produto"))
    st.plotly_chart(px.bar(df, x="Cliente", y="Total", title="Vendas por Cliente"))

    # Gerar PDF do relatório filtrado
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margem_esquerda = 50
    margem_direita = width - 50
    linha_inicial = height - 80
    espacamento_linhas = 20
    y = linha_inicial
    pagina_atual = 1

    # Função para desenhar cabeçalho
    def desenhar_cabecalho():
        nonlocal y
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawCentredString(width / 2, y, "Relatório de Vendas - NS Lanches")
        y -= espacamento_linhas
        pdf.setFont("Helvetica", 12)
        periodo_texto = f"Período: {data_inicial.strftime('%d/%m/%Y')} até {data_final.strftime('%d/%m/%Y')}"
        pdf.drawCentredString(width / 2, y, periodo_texto)
        y -= espacamento_linhas
        pdf.setLineWidth(1)
        pdf.line(margem_esquerda, y, margem_direita, y)
        y -= espacamento_linhas
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(margem_esquerda, y, "Data")
        pdf.drawString(margem_esquerda + 100, y, "Cliente")
        pdf.drawString(margem_esquerda + 250, y, "Produto")
        pdf.drawRightString(margem_direita - 140, y, "Qtde")
        pdf.drawRightString(margem_direita - 80, y, "Total (R$)")
        y -= espacamento_linhas
        pdf.setLineWidth(0.5)
        pdf.line(margem_esquerda, y + 5, margem_direita, y + 5)
        pdf.setFont("Helvetica", 11)

    # Função para desenhar rodapé com número da página
    def desenhar_rodape(pagina_num):
        pdf.setFont("Helvetica-Oblique", 9)
        texto_rodape = f"Página {pagina_num}"
        pdf.drawRightString(margem_direita, 30, texto_rodape)

    desenhar_cabecalho()

    for index, row in df.iterrows():
        if y < 50:  # Quebra de página
            desenhar_rodape(pagina_atual)
            pdf.showPage()
            pagina_atual += 1
            y = linha_inicial
            desenhar_cabecalho()

        pdf.drawString(margem_esquerda, y, row['Data'][:19])  # Data com até segundos
        pdf.drawString(margem_esquerda + 100, y, str(row['Cliente']))
        pdf.drawString(margem_esquerda + 250, y, str(row['Produto']))
        pdf.drawRightString(margem_direita - 140, y, str(row['Quantidade']))
        pdf.drawRightString(margem_direita - 80, y, f"{row['Total']:.2f}")
        y -= espacamento_linhas

    # Linha final e rodapé
    pdf.setLineWidth(1)
    pdf.line(margem_esquerda, y + 10, margem_direita, y + 10)
    desenhar_rodape(pagina_atual)

    pdf.save()
    buffer.seek(0)
    st.download_button("📥 Baixar Relatório PDF", buffer, file_name="relatorio_vendas.pdf")

menu = {
    "Início": pagina_inicio,
    "Empresa": pagina_empresa,
    "Clientes": pagina_clientes,
    "Produtos": pagina_produtos,
    "Vendas": pagina_vendas,
    "Cancelar Venda": pagina_cancelar_venda,
    "Relatórios": pagina_relatorios
}

if not st.session_state.logado:
    pagina_login()
else:
    st.sidebar.title("Menu")
    escolha = st.sidebar.radio("Navegação", list(menu.keys()))
    st.session_state.pagina = escolha
    menu[escolha]()
