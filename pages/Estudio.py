# Arquivo: pages/2_🎬_Estudio.py
import streamlit as st
import utils
import os

st.set_page_config(page_title="Estúdio", page_icon="🎬", layout="wide")
st.title("🎬 Estúdio de Produção")

# Verifica se tem roteiro
if not st.session_state['texto_completo_pt']:
    st.error("🚫 Nenhum roteiro encontrado! Vá para a página 'Roteirização' primeiro.")
    st.stop()

st.info("Roteiro carregado da memória. Configure a renderização abaixo.")

col_preview, col_action = st.columns([1, 2])
with col_preview:
    st.subheader("Configuração")
    preview_mode = st.checkbox("Modo Preview (Apenas 1 min)", value=True, help="Gera rápido para testar.")
    tema_atual = st.text_input("Texto para Capa", value="Nova História")

with col_action:
    st.subheader("Ações")
    
    # Passo 1: Assets
    if st.button("1. Gerar Áudios e Capa"):
        with st.spinner("Criando capa..."):
            capa = utils.gerar_capa_simples(tema_atual, "História IA")
            st.session_state['imagem_capa_path'] = capa
            st.image(capa, width=200)
        
        with st.spinner("Gerando Áudios (Edge TTS)..."):
            utils.gerar_audio(st.session_state['texto_completo_en'], "en")
            utils.gerar_audio(st.session_state['texto_completo_pt'], "pt")
        
        st.success("Assets gerados na pasta /temp!")

    # Passo 2: Render
    if st.button("2. Renderizar Vídeos (.MP4)"):
        if not os.path.exists("temp/audio_pt.mp3"):
            st.error("Gere os áudios primeiro!")
        else:
            prog = st.progress(0)
            
            with st.spinner("Renderizando PT-BR..."):
                file_pt = utils.renderizar_video("temp/audio_pt.mp3", st.session_state['imagem_capa_path'], "pt", preview_mode)
                st.video(file_pt)
            
            prog.progress(50)
            
            with st.spinner("Renderizando English..."):
                file_en = utils.renderizar_video("temp/audio_en.mp3", st.session_state['imagem_capa_path'], "en", preview_mode)
                st.video(file_en)
            
            prog.progress(100)
            st.balloons()
