import os
import subprocess
from datetime import date, timedelta
from playwright.sync_api import sync_playwright
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega as variáveis do arquivo .env
load_dotenv()

# Credenciais do Supabase puxadas corretamente pelo nome da variável
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
EMAIL = os.getenv("CLINICA_EMAIL")
SENHA = os.getenv("CLINICA_SENHA")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def executar_automacao():
    print("Verificando/instalando o navegador do Playwright...")
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        print(f"Aviso na instalação do navegador: {e}")

    print("Iniciando automação do Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=500)
        page = browser.new_page()

        print("Acessando o site...")
        page.goto("https://app2.clinicaagil.com.br/login")

        print("Aguardando o carregamento do formulário de login...")
        # Aguarda o campo de texto aparecer explicitamente na tela antes de preencher
        page.wait_for_selector("input[type='text']", timeout=15000)

        print("Preenchendo credenciais...")
        # Preenche com segurança usando os seletores corretos
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
        
        page.get_by_role("button", name="Selecione o período ").click()
        page.get_by_role("listitem").filter(has_text="Últimos 30 dias").click()

        print("Aguardando e baixando o arquivo Excel...")
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Gerar Excel").click()
        
        download = download_info.value
        caminho_excel = "relatorio_financeiro.xlsx"
        download.save_as(caminho_excel)
        print(f"Excel salvo com sucesso em: {caminho_excel}")

        browser.close()

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

        # Limpa os dados antigos e envia os novos para o Supabase
        supabase.table("atendimentos").delete().neq("id", 0).execute()
        dados_para_inserir = df_filtrado.to_dict(orient="records")
        supabase.table("atendimentos").insert(dados_para_inserir).execute()

        print("Dados enviados para o Supabase com sucesso!")
        return True
    else:
        print("Erro ao mapear as colunas no Excel.")
        return False

if __name__ == "__main__":
    executar_automacao()