import streamlit as st
import sqlite3
from datetime import datetime
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import pandas as pd
import plotly.express as px

# --- Banco de dados ---
conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

def criar_tabelas():
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
    # Insere usuário admin padrão se tabela estiver vazia
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

criar_tabelas()

# --- Estado e Layout ---
if "logado" not in st.session_state:
    st.session_state.logado = False
if "pagina" not in st.session_state:
    st.session_state.pagina = "Início"
if "logo" not in st.session_state:
    st.session_state.logo = None
if "cor_botao" not in st.session_state:
    st.session_state.cor_botao = "#FF7F00"  # Laranja padrão

def botao_laranja(label, key=None):
    return st.button(label, key=key, help=None, on_click=None, args=None, kwargs=None,
                     type="secondary", use_container_width=True, 
                     help_color=st.session_state.cor_botao)

# --- Login ---
def pagina_login():
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

# --- Menu lateral ---
def menu_lateral():
    with st.sidebar:
        st.title("NS Sistemas")
        if st.session_state.logo:
            st.image(st.session_state.logo, width=150)
        else:
            st.write("Carregue o logo abaixo")

        logo_upload = st.file_uploader("Logo da empresa", type=["png", "jpg", "jpeg"], key="upload_logo")
        if logo_upload:
            st.session_state.logo = logo_upload

        st.markdown("---")
        # Botões laranja, com cor customizável
        if st.button("Início", key="btn_inicio"):
            st.session_state.pagina = "Início"
        if st.button("Empresa", key="btn_empresa"):
            st.session_state.pagina = "Empresa"
        if st.button("Clientes", key="btn_clientes"):
            st.session_state.pagina = "Clientes"
        if st.button("Produtos", key="btn_produtos"):
            st.session_state.pagina = "Produtos"
        if st.button("Vendas", key="btn_vendas"):
            st.session_state.pagina = "Vendas"
        if st.button("Cancelar Venda", key="btn_cancelar"):
            st.session_state.pagina = "Cancelar Venda"
        if st.button("Relatórios", key="btn_relatorios"):
            st.session_state.pagina = "Relatórios"

        st.markdown("---")
        st.subheader("Configurações")
        cor = st.color_picker("Cor dos botões", st.session_state.cor_botao)
        if cor != st.session_state.cor_botao:
            st.session_state.cor_botao = cor

# --- Páginas ---
def pagina_inicio():
    st.title("Bem-vindo ao NS Sistemas!")
    cursor.execute("SELECT nome, cnpj FROM empresa ORDER BY id DESC LIMIT 1")
    empresa = cursor.fetchone()
    if empresa:
        st.markdown(f"**Empresa:** {empresa[0]}")
        st.markdown(f"**CNPJ:** {empresa[1]}")
    else:
        st.warning("Nenhuma empresa cadastrada.")

def pagina_empresa():
    st.title("Cadastro de Empresa")
    nome = st.text_input("Nome da Empresa")
    cnpj = st.text_input("CNPJ")
    if st.button("Salvar Empresa"):
        if nome and cnpj:
            cursor.execute("INSERT INTO empresa (nome, cnpj) VALUES (?, ?)", (nome, cnpj))
            conn.commit()
            st.success("Empresa cadastrada com sucesso!")
        else:
            st.warning("Preencha todos os campos.")

def pagina_clientes():
    st.title("Cadastro de Clientes")
    nome = st.text_input("Nome")
    cpf = st.text_input("CPF")
    telefone = st.text_input("Telefone")
    endereco = st.text_area("Endereço")
    if st.button("Cadastrar Cliente"):
        if nome:
            cursor.execute("INSERT INTO clientes (nome, cpf, telefone, endereco) VALUES (?, ?, ?, ?)",
                           (nome, cpf, telefone, endereco))
            conn.commit()
            st.success("Cliente cadastrado com sucesso!")
        else:
            st.warning("Informe o nome do cliente")

def pagina_produtos():
    st.title("Cadastro de Produtos")
    nome = st.text_input("Nome do Produto")
    preco = st.number_input("Preço", min_value=0.0, step=0.01)
    estoque = st.number_input("Estoque", min_value=0, step=1)
    unidade = st.selectbox("Unidade", ["Unidade", "Peso"])
    categoria = st.text_input("Categoria")
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if st.button("Cadastrar Produto"):
        if nome:
            cursor.execute("INSERT INTO produtos (nome, preco, estoque, unidade, categoria, data) VALUES (?, ?, ?, ?, ?, ?)",
                           (nome, preco, estoque, unidade, categoria, data))
            conn.commit()
            st.success("Produto cadastrado com sucesso!")
        else:
            st.warning("Informe o nome do produto")

    st.markdown("### Produtos Cadastrados")
    df = pd.read_sql("SELECT id, nome, preco, estoque, categoria FROM produtos", conn)
    for i, row in df.iterrows():
        col1, col2 = st.columns([4,1])
        with col1:
            st.write(f"**{row['nome']}** | Preço: R$ {row['preco']:.2f} | Estoque: {row['estoque']} | Categoria: {row['categoria']}")
        with col2:
            if st.button(f"Excluir {row['id']}", key=f"excluir_{row['id']}"):
                cursor.execute("DELETE FROM produtos WHERE id=?", (row['id'],))
                conn.commit()
                st.success("Produto excluído com sucesso")
                st.experimental_rerun()

def pagina_vendas():
    st.title("Registrar Venda")
    produtos = [r[0] for r in cursor.execute("SELECT nome FROM produtos").fetchall()]
    clientes = [r[0] for r in cursor.execute("SELECT nome FROM clientes").fetchall()]
    formas_pagamento = ["Dinheiro", "Cartão", "PIX"]

    if not produtos or not clientes:
        st.info("Cadastre produtos e clientes antes de registrar vendas")
        return

    produto = st.selectbox("Produto", produtos)
    preco, estoque, unidade, categoria = cursor.execute(
        "SELECT preco, estoque, unidade, categoria FROM produtos WHERE nome=?", (produto,)).fetchone()
    st.write(f"Preço: R$ {preco:.2f} | Estoque: {estoque} | Unidade: {unidade} | Categoria: {categoria}")

    cliente = st.selectbox("Cliente", clientes)
    telefone, endereco = cursor.execute("SELECT telefone, endereco FROM clientes WHERE nome=?", (cliente,)).fetchone()
    st.write(f"Telefone: {telefone} | Endereço: {endereco}")

    forma_pagamento = st.selectbox("Forma de Pagamento", formas_pagamento)
    quantidade = st.number_input("Quantidade", min_value=1, step=1)

    if st.button("Finalizar Venda"):
        if quantidade > estoque:
            st.warning("Estoque insuficiente")
        else:
            total = preco * quantidade
            data_venda = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO vendas (data, produto, cliente, quantidade, total) VALUES (?, ?, ?, ?, ?)",
                           (data_venda, produto, cliente, quantidade, total))
            cursor.execute("UPDATE produtos SET estoque=estoque-? WHERE nome=?", (quantidade, produto))
            conn.commit()

            # Gera comprovante PDF
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            c.drawString(100, 800, "NS SISTEMAS - COMPROVANTE DE VENDA")
            c.drawString(100, 780, f"Data: {data_venda}")
            c.drawString(100, 760, f"Cliente: {cliente}")
            c.drawString(100, 740, f"Endereço: {endereco}")
            c.drawString(100, 720, f"Telefone: {telefone}")
            c.drawString(100, 700, f"Produto: {produto}")
            c.drawString(100, 680, f"Quantidade: {quantidade}")
            c.drawString(100, 660, f"Forma de Pagamento: {forma_pagamento}")
            c.drawString(100, 640, f"Total: R$ {total:.2f}")
            c.save()
            st.download_button("Baixar Comprovante em PDF", buffer.getvalue(), file_name="comprovante.pdf")
            st.success("Venda registrada com sucesso!")

def pagina_cancelar_venda():
    st.title("Cancelar Venda")
    data_inicio = st.date_input("Data Inicial")
    data_fim = st.date_input("Data Final")

    vendas = cursor.execute("SELECT id, data, produto, cliente, quantidade, total FROM vendas").fetchall()
    vendas_filtradas = [v for v in vendas if data_inicio.strftime("%Y-%m-%d") <= v[1][:10] <= data_fim.strftime("%Y-%m-%d")]

    st.write("### Vendas no Período")
    df = pd.DataFrame(vendas_filtradas, columns=["ID", "Data", "Produto", "Cliente", "Quantidade", "Total"])
    st.dataframe(df)

    # Excluir venda ao clicar (se quiser implementar)
    for v in vendas_filtradas:
        if st.button(f"Cancelar Venda ID {v[0]}"):
            cursor.execute("DELETE FROM vendas WHERE id=?", (v[0],))
            # Ajusta estoque do produto
            cursor.execute("UPDATE produtos SET estoque=estoque+? WHERE nome=?", (v[4], v[2]))
            conn.commit()
            st.success("Venda cancelada e estoque atualizado")
            st.experimental_rerun()

def pagina_relatorios():
    st.title("Relatórios de Vendas")
    data_inicio = st.date_input("Data inicial")
    data_fim = st.date_input("Data final")

    vendas = cursor.execute("SELECT data, produto, cliente, quantidade, total FROM vendas").fetchall()
    df = [v for v in vendas if data_inicio.strftime("%Y-%m-%d") <= v[0][:10] <= data_fim.strftime("%Y-%m-%d")]

    if not df:
        st.info("Nenhuma venda no período selecionado")
        return

    st.write("### Vendas no Período")
    df_vendas = pd.DataFrame(df, columns=["Data", "Produto", "Cliente", "Quantidade", "Total"])
    st.dataframe(df_vendas)

    total = df_vendas["Total"].sum()
    st.success(f"Total vendido no período: R$ {total:.2f}")

    df_vendas["Data"] = pd.to_datetime(df_vendas["Data"])
    grafico = px.bar(df_vendas, x="Data", y="Total", color="Produto", title="Vendas por Produto")
    st.plotly_chart(grafico)

    # Gerar PDF do relatório
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

# --- Fluxo principal ---
def main():
    if not st.session_state.logado:
        pagina_login()
    else:
        menu_lateral()
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
        elif pagina == "Cancelar Venda":
            pagina_cancelar_venda()
        elif pagina == "Relatórios":
            pagina_relatorios()
        else:
            st.write("Página não encontrada")

if __name__ == "__main__":
    main()
