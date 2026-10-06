import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

# Configuração da página para ocupar a largura total e permitir adaptação mobile
st.set_page_config(page_title="Dashboard Financeiro", layout="wide", initial_sidebar_state="collapsed")

# Estilização CSS leve para melhorar o visual em celulares
st.markdown("""
    <style>
        .main {
            padding: 0rem 1rem;
        }
        h1 {
            font-size: 1.8rem !important;
        }
        @media (max-width: 768px) {
            .stMetric {
                font-size: 0.9rem !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

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
    
    # Métricas responsivas (empilham automaticamente ou dividem bem o espaço)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💰 Faturamento Total", f"R$ {total_faturamento:,.2f}")
    with col2:
        st.metric("📋 Total de Atendimentos", f"{total_atendimentos}")
    
    st.markdown("---")

    st.subheader("Faturamento por Profissional")
    
    faturamento_prof = df.groupby('Profissional')['Valor Total'].sum().reset_index()
    # Ordena do menor para o maior para que o maior fique no topo no gráfico horizontal
    faturamento_prof = faturamento_prof.sort_values(by='Valor Total', ascending=True)
    
    # Gráfico de barras horizontal, perfeito para nomes longos e celulares
    fig_prof = px.bar(
        faturamento_prof, 
        x='Valor Total', 
        y='Profissional', 
        orientation='h',
        text_auto='.2s', 
        color='Profissional'
    )
    
    fig_prof.update_layout(
        height=500,           # Altura proporcional para listar todos os profissionais
        showlegend=False,     # Remove a legenda lateral desnecessária
        margin=dict(l=10, r=10, t=10, b=10), # Margens compactas
        xaxis_title="Valor Total (R$)",
        yaxis_title=""
    )
    
    st.plotly_chart(fig_prof, use_container_width=True)

else:
    st.warning("⚠️ Ainda não há dados gravados na base de dados do Supabase.")