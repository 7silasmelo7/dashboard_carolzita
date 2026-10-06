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

# Conexão com o Supabase
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
@st.cache_data(ttl=600)
def carregar_dados_do_supabase():
    try:
        resposta = supabase.table("atendimentos").select("*").execute()
        dados = resposta.data
        if not dados:
            return pd.DataFrame()
        
        df = pd.DataFrame(dados)
        df = df.rename(columns={'data': 'Data', 'profissional': 'Profissional', 'valor_total': 'Valor Total'})
        
        # Conversão de data flexível e automática (corrige qualquer falha de formato)
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce', dayfirst=True)
        
        # Remove linhas onde a data não pôde ser convertida
        df = df.dropna(subset=['Data'])
        
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
    
    fig_prof = px.pie(
        faturamento_prof, 
        names='Profissional', 
        values='Valor Total',
        hole=0.4 # Cria um efeito de rosca, que se adapta lindamente a ecrãs verticais
    )
    
    fig_prof.update_layout(
        height=450,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(
            orientation="h",       # Legenda na horizontal na parte inferior para não espremer o gráfico
            yanchor="bottom", 
            y=-0.3, 
            xanchor="center", 
            x=0.5
        )
    )
    
    st.plotly_chart(fig_prof, width='stretch')

    st.markdown("---")

    # --- SEÇÃO DE CARDS DOS ÚLTIMOS 7 DIAS ---
    st.subheader("🔥 Desempenho (Últimos 7 Dias)")
    
    # Identifica a data mais recente da base para servir de âncora (ex: 06/10/2026)
    data_referencia = df['Data'].max()
    data_limite_7_dias = data_referencia - pd.Timedelta(days=7)
    
    # Filtra rigorosamente os dados apenas dos últimos 7 dias do relatório
    df_ultimos_7 = df[(df['Data'] >= data_limite_7_dias) & (df['Data'] <= data_referencia)]
    
    if not df_ultimos_7.empty:
        # Agrupa por profissional calculando o faturamento e a contagem exata de atendimentos
        resumo_7_dias = df_ultimos_7.groupby('Profissional').agg(
            Faturamento_Total=('Valor Total', 'sum'),
            Qtd_Atendimentos=('Valor Total', 'count')
        ).reset_index()
        
        # Ordena do maior faturamento para o menor
        resumo_7_dias = resumo_7_dias.sort_values(by='Faturamento_Total', ascending=False)
        
        # Exibe em formato de cards limpos e responsivos para celular
        for index, row in resumo_7_dias.iterrows():
            profissional = row['Profissional']
            valor = row['Faturamento_Total']
            qtd_atendimentos = int(row['Qtd_Atendimentos'])
            
            st.markdown(f"""
                <div class="profissional-card">
                    <strong style="font-size: 1.1rem; color: #ffffff;">👤 {profissional}</strong><br>
                    <span style="color: #4CAF50; font-size: 1.2rem; font-weight: bold;">R$ {valor:,.2f}</span><br>
                    <span style="color: #aaaaaa; font-size: 0.9rem;">📋 <b>{qtd_atendimentos}</b> atendimentos nos últimos 7 dias</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Não há registros suficientes para o período recente.")

else:
    st.warning("⚠️ Ainda não há dados gravados na base de dados do Supabase.")