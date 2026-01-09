import streamlit as st
import google.generativeai as genai
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fábrica de Histórias IA", page_icon="🎬", layout="centered")

st.title("🎬 Gerador de Histórias (MVP)")
st.caption("Powered by Gemini 2.5 Flash")

# --- CONFIGURAÇÃO DA API (VIA SECRETS) ---
try:
    # Busca a chave diretamente nos segredos do Streamlit
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("⚠️ Erro de Configuração: API Key não encontrada.")
    st.info("Certifique-se de que você criou o arquivo `.streamlit/secrets.toml` com a linha: `GOOGLE_API_KEY = 'sua-chave'`")
    st.stop()

# --- INPUTS DO USUÁRIO ---
with st.container(border=True):
    st.subheader("Configuração do Roteiro")
    col1, col2 = st.columns(2)
    with col1:
        nicho = st.selectbox("Escolha o Nicho:", ["Histórias Bíblicas", "Mistério/Curiosidades"])
    with col2:
        idioma_base = st.selectbox("Idioma Principal:", ["Português", "Inglês"])

    tema = st.text_input("Sobre o que é a história?", placeholder="Ex: A coragem de Davi contra Golias")

# --- FUNÇÃO GERADORA (GEMINI 2.5 FLASH) ---
def gerar_historia(nicho, tema, idioma):
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Você é um roteirista viral especialista em YouTube Shorts e TikTok.
    Crie uma história narrada para o nicho: {nicho}.
    Tema: {tema}.
    Idioma: {idioma}.
    
    Regras OBRIGATÓRIAS:
    1. O texto deve ter no máximo 130 palavras (para dar aprox 50-60 segundos de áudio).
    2. Comece com uma frase de impacto (Gancho) nos primeiros 3 segundos.
    3. Linguagem simples, engajadora e emocionante.
    4. Não coloque indicações de cena, música ou pausas (ex: [pausa dramática]), apenas o texto puro da narração.
    5. Retorne APENAS o texto da história, nada mais.
    """
    
    with st.spinner(f'O Gemini 2.5 está escrevendo em {idioma}...'):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            st.error(f"Erro ao conectar com Gemini: {e}")
            return None

# --- BOTÃO DE AÇÃO ---
if st.button("✨ Gerar Roteiro", type="primary", use_container_width=True):
    if not tema:
        st.warning("Por favor, escreva um tema para começar.")
    else:
        historia = gerar_historia(nicho, tema, idioma_base)
        
        if historia:
            # Salva na sessão
            st.session_state['historia_gerada'] = historia
            st.session_state['nicho_atual'] = nicho
            
            st.success("Roteiro Criado!")
            st.text_area("Roteiro Final:", value=historia, height=300)

# --- INDICAÇÃO DE PRÓXIMOS PASSOS ---
if 'historia_gerada' in st.session_state:
    st.divider()
    st.info("🔽 Próxima Etapa: Gerar Áudio (Edge-TTS) e Imagem (Gemini 2.5) para este texto.")
