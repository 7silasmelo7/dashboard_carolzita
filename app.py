import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

st.set_page_config(page_title="Dashboard Financeiro", layout="wide")
st.title("📊 Dashboard Carolzita")

# Conexão com o Supabase (puxa dos Secrets na nuvem ou do .env local)
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
except:
    import os
    from dotenv import load_dotenv
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

# Função para ler os dados do Supabase com cache
@st.cache_data(ttl=600) # Atualiza o cache a cada 10 minutos
def carregar_dados_do_supabase():
    try:
        resposta = supabase.table("atendimentos").select("*").execute()
        dados = resposta.data
        if not dados:
            return pd.DataFrame()
        
        df = pd.DataFrame(dados)
        # Padroniza os nomes das colunas para o restante do código
        df = df.rename(columns={'data': 'Data', 'profissional': 'Profissional', 'valor_total': 'Valor Total'})
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

df = carregar_dados_do_supabase()

if not df.empty:
    total_faturamento = df['Valor Total'].sum()
    total_atendimentos = len(df)
    
    col1, col2 = st.columns(2)
    col1.metric("💰 Faturamento Total", f"R$ {total_faturamento:,.2f}")
    col2.metric("📋 Total de Atendimentos", f"{total_atendimentos}")
    
    st.markdown("---")

    st.subheader("Faturamento por Profissional")
    
    faturamento_prof = df.groupby('Profissional')['Valor Total'].sum().reset_index()
    faturamento_prof = faturamento_prof.sort_values(by='Valor Total', ascending=False)
    
    fig_prof = px.bar(
        faturamento_prof, 
        x='Profissional', 
        y='Valor Total', 
        text_auto='.2s', 
        color='Profissional'
    )
    
    fig_prof.update_layout(
        height=550,
        xaxis_tickangle=-25,
        showlegend=True
    )
    
    st.plotly_chart(fig_prof, use_container_width=True)

else:
    st.warning("⚠️ Ainda não há dados gravados na base de dados do Supabase.")