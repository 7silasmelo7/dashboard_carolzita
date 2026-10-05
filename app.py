import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import subprocess
import os

st.set_page_config(page_title="Dashboard Financeiro", layout="wide")
st.title("📊 Dashboard Carolzita")

# --- BOTÃO DE ATUALIZAÇÃO NA BARRA LATERAL ---
st.sidebar.header("Painel de Controle")
if st.sidebar.button("🔄 Atualizar Dados do Sistema"):
    with st.spinner("Executando robô e baixando novos dados... Isso pode levar alguns segundos."):
        resultado = subprocess.run(["python", "robo.py"], capture_output=True, text=True)
        if resultado.returncode == 0:
            st.sidebar.success("Dados atualizados com sucesso!")
            st.cache_data.clear()
            st.rerun()
        else:
            st.sidebar.error("Erro ao executar o robô. Verifique o terminal.")

# Função para ler os dados do SQLite com segurança
@st.cache_data
def carregar_dados_do_banco():
    try:
        conexao = sqlite3.connect('clinica.db')
        query = "SELECT * FROM atendimentos"
        df = pd.read_sql(query, conexao)
        conexao.close()
        
        # Formata a data
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        return df
    except Exception:
        return pd.DataFrame()

df = carregar_dados_do_banco()

if not df.empty:
    # Métricas gerais no topo
    total_faturamento = df['Valor Total'].sum()
    total_atendimentos = len(df)
    
    col1, col2 = st.columns(2)
    col1.metric("💰 Faturamento Total", f"R$ {total_faturamento:,.2f}")
    col2.metric("📋 Total de Atendimentos", f"{total_atendimentos}")
    
    st.markdown("---")

    # --- GRÁFICO DE BARRAS VERTICAIS IDÊNTICO À REFERÊNCIA ---
    st.subheader("Faturamento por Profissional")
    
    # Agrupa, soma e ORDENA do maior para o menor faturamento (decrescente)
    faturamento_prof = df.groupby('Profissional')['Valor Total'].sum().reset_index()
    faturamento_prof = faturamento_prof.sort_values(by='Valor Total', ascending=False)
    
    # Cria o gráfico de barras verticais com a mesma identidade visual
    fig_prof = px.bar(
        faturamento_prof, 
        x='Profissional', 
        y='Valor Total', 
        text_auto='.2s', 
        color='Profissional'
    )
    
    # Ajustes finos de layout para imitar o modelo da imagem (inclinação, altura e legenda lateral)
    fig_prof.update_layout(
        height=550,
        xaxis_tickangle=-25,  # Inclina os nomes para caberem perfeitamente
        showlegend=True       # Exibe a legenda lateral com as cores de cada profissional
    )
    
    st.plotly_chart(fig_prof, use_container_width=True)

else:
    st.warning("⚠️ Ainda não há dados gravados no banco de dados ('clinica.db'). Clique no botão **'Atualizar Dados do Sistema'** na barra lateral para rodar o robô pela primeira vez!")