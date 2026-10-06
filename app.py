import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

# Configuração da página otimizada para mobile
st.set_page_config(page_title="Dashboard Financeiro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        .profissional-card {
            background-color: #1e1e1e;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            border: 1px solid #333;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard Carolzita")

# Conexão com o Supabase (puxa dos Secrets na nuvem ou do .env local)[cite: 2]
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

# Função para ler os dados do Supabase com cache[cite: 2]
@st.cache_data(ttl=600)
def carregar_dados_do_supabase():
    try:
        resposta = supabase.table("atendimentos").select("*").execute()
        dados = resposta.data
        if not dados:
            return pd.DataFrame()
        
        df = pd.DataFrame(dados)
        df = df.rename(columns={'data': 'Data', 'profissional': 'Profissional', 'valor_total': 'Valor Total'})
        df['Data'] = pd.to_datetime(df['Data'], format='%Y-%m-%d', errors='coerce')
        if df['Data'].isnull().all():
            df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

df = carregar_dados_do_supabase()

if not df.empty:
    total_faturamento = df['Valor Total'].sum()
    total_atendimentos = len(df)
    
    # Métricas principais no topo
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💰 Faturamento Total", f"R$ {total_faturamento:,.2f}")
    with col2:
        st.metric("📋 Total de Atendimentos", f"{total_atendimentos}")
    
    st.markdown("---")

    # Gráfico Geral de Faturamento por Profissional (Horizontal)
    st.subheader("Faturamento Geral por Profissional")
    
    faturamento_prof = df.groupby('Profissional')['Valor Total'].sum().reset_index()
    faturamento_prof = faturamento_prof.sort_values(by='Valor Total', ascending=True)
    
    fig_prof = px.bar(
        faturamento_prof, 
        x='Valor Total', 
        y='Profissional', 
        orientation='h',
        text_auto='.2s', 
        color='Profissional'
    )
    
    fig_prof.update_layout(
        height=450,
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="Valor Total (R$)",
        yaxis_title=""
    )
    
    st.plotly_chart(fig_prof, use_container_width=True)

    st.markdown("---")

    # --- SEÇÃO DE CARDS DOS ÚLTIMOS 7 DIAS ---
    st.subheader("🔥 Desempenho (Últimos 7 Dias)")
    
    # Define a data de corte com base na última data registrada no sistema
    data_mais_recente = df['Data'].max()
    data_limite_7_dias = data_mais_recente - pd.Timedelta(days=7)
    
    # Filtra apenas os dados dos últimos 7 dias
    df_ultimos_7 = df[df['Data'] >= data_limite_7_dias]
    
    if not df_ultimos_7.empty:
        fat_7_dias = df_ultimos_7.groupby('Profissional')['Valor Total'].sum().reset_index()
        fat_7_dias = fat_7_dias.sort_values(by='Valor Total', ascending=False)
        
        # Exibe em formato de cards limpos para celular
        for index, row in fat_7_dias.iterrows():
            profissional = row['Profissional']
            valor = row['Valor Total']
            
            # Conta quantos atendimentos o profissional fez nos últimos 7 dias
            qtd_atendimentos = len(df_ultimos_7[df_ultimos_7['Profissional'] == profissional])
            
            st.markdown(f"""
                <div class="profissional-card">
                    <strong style="font-size: 1.1rem; color: #ffffff;">👤 {profissional}</strong><br>
                    <span style="color: #4CAF50; font-size: 1.2rem; font-weight: bold;">R$ {valor:,.2f}</span> 
                    <span style="color: #aaaaaa; font-size: 0.9rem;">({qtd_atendimentos} atendimentos nos últimos 7 dias)</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Não há registros suficientes nos últimos 7 dias.")

else:
    st.warning("⚠️ Ainda não há dados gravados na base de dados do Supabase.")