import streamlit as st
import google.generativeai as genai
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fábrica de Histórias IA", page_icon="🎬")

st.title("🎬 Gerador de Histórias (MVP)")

# --- CONFIGURAÇÃO DA API (GEMINI) ---
# Tenta pegar dos segredos do Streamlit (nuvem) ou input lateral (local)
api_key = st.sidebar.text_input("Cole sua Google API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
else:
    if 'GOOGLE_API_KEY' in st.secrets:
        genai.configure(api_key=st.secrets['GOOGLE_API_KEY'])
    else:
        st.warning("Por favor, insira sua API Key na barra lateral para começar.")
        st.stop()

# --- INPUTS DO USUÁRIO ---
nicho = st.selectbox("Escolha o Nicho:", ["Histórias Bíblicas", "Mistério/Curiosidades"])
tema = st.text_input("Sobre o que é a história?", placeholder="Ex: A coragem de Davi contra Golias")

# --- FUNÇÃO GERADORA (GEMINI 1.5 FLASH) ---
def gerar_historia(nicho, tema):
    # Modelo rápido e barato (ou free)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Você é um roteirista especialista em YouTube Shorts e TikTok.
    Crie uma história narrada para o nicho: {nicho}.
    Tema: {tema}.
    
    Regras OBRIGATÓRIAS:
    1. O texto deve ter no máximo 130 palavras (para dar aprox 50-60 segundos de áudio).
    2. Comece com uma frase de impacto (Gancho) nos primeiros 3 segundos.
    3. Linguagem simples, engajadora e emocionante.
    4. Não coloque indicações de cena como [Cena 1], apenas o texto corrido da narração.
    5. Retorne APENAS o texto da história, nada mais.
    """
    
    with st.spinner('O Gemini está escrevendo...'):
        response = model.generate_content(prompt)
        return response.text

# --- BOTÃO DE AÇÃO ---
if st.button("Gerar Roteiro"):
    if not tema:
        st.error("Escreva um tema primeiro!")
    else:
        historia = gerar_historia(nicho, tema)
        
        # Salva na sessão para não perder quando recarregar
        st.session_state['historia_pt'] = historia
        st.session_state['historia_en'] = "Tradução pendente..." # Faremos isso no próximo passo
        
        st.success("Roteiro Criado!")
        st.subheader("📜 Roteiro em Português:")
        st.write(st.session_state['historia_pt'])

# --- ÁREA DE DEBUG (Para vermos se está funcionando) ---
if 'historia_pt' in st.session_state:
    st.info("Próximo passo: Gerar Áudio e Imagem para este texto.")
