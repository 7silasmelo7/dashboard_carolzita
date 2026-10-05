import os
import subprocess
import sys

# --- INSTALAÇÃO AUTOMÁTICA DE EMERGÊNCIA NA NUVEM ---
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright não encontrado. Instalando automaticamente...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.check_call(["playwright", "install", "chromium"])
    from playwright.sync_api import sync_playwright

from datetime import date, timedelta
import pandas as pd
import sqlite3
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Tenta pegar do Streamlit Cloud (secrets) ou do arquivo .env local
try:
    import streamlit as st
    EMAIL = st.secrets["CLINICA_EMAIL"]
    SENHA = st.secrets["CLINICA_SENHA"]

except:
    EMAIL = os.getenv("CLINICA_EMAIL")
    SENHA = os.getenv("CLINICA_SENHA")

def executar_automacao():

    print("Verificando/instalando o navegador do Playwright...")
    try:
        # Força o download do Chromium caso ele não exista no servidor de nuvem
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        print(f"Aviso na instalação do navegador: {e}")

    print("Iniciando automação do Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()

        print("Acessando o site...")
        page.goto("https://app2.clinicaagil.com.br/login")

        print("Preenchendo credenciais...")
        # Usa as variáveis protegidas
        page.fill("input[type='text']", EMAIL)
        page.fill("input[type='password']", SENHA)

        print("Clicando no botão de entrar...")
        page.click("form button[type='submit']")

        page.wait_for_timeout(5000)

        print("Navegando até relatórios...")
        page.get_by_role("link", name="Outros").click()
        page.wait_for_timeout(2000)
        page.get_by_role("link", name=" Relatórios").click()
        page.wait_for_timeout(2000)
        
        # Selecionando o período de 30 dias atrás
        page.get_by_role("button", name="Selecione o período ").click()
        page.get_by_role("listitem").filter(has_text="Últimos 30 dias").click()

        # --- CAPTURANDO O DOWNLOAD DO EXCEL ---
        print("Aguardando e baixando o arquivo Excel...")
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Gerar Excel").click()
        
        download = download_info.value
        caminho_excel = "relatorio_financeiro.xlsx"
        download.save_as(caminho_excel)
        print(f"Excel salvo com sucesso em: {caminho_excel}")

        browser.close()

    # --- PROCESSANDO O EXCEL PARA O BANCO DE DADOS ---
    print("Processando dados para o banco...")
    xls = pd.ExcelFile(caminho_excel)
    nome_aba = 'Atendimentos' if 'Atendimentos' in xls.sheet_names else xls.sheet_names[0]
    df = pd.read_excel(caminho_excel, sheet_name=nome_aba)

    colunas_desejadas = {}
    for col in df.columns:
        col_str = str(col).strip()
        if col_str == 'Data':
            colunas_desejadas['Data'] = col
        elif col_str == 'Profissional':
            colunas_desejadas['Profissional'] = col
        elif col_str == 'Valor Total':
            colunas_desejadas['Valor Total'] = col

    if len(colunas_desejadas) == 3:
        df_filtrado = pd.DataFrame()
        for chave, original in colunas_desejadas.items():
            df_filtrado[chave] = df[original]
        
        df_filtrado = df_filtrado.dropna(subset=['Data'])

        # Atualiza o banco SQLite
        conexao = sqlite3.connect('clinica.db')
        df_filtrado.to_sql('atendimentos', conexao, if_exists='replace', index=False)
        conexao.close()
        print("Banco de dados atualizado com sucesso!")
        return True
    else:
        print("Erro ao mapear as colunas no Excel.")
        return False