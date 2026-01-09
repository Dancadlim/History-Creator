import streamlit as st
import utils
import os

st.set_page_config(page_title="Estúdio", page_icon="🎬", layout="wide")
st.title("🎬 Estúdio de Produção")

if not st.session_state['texto_completo_pt']:
    st.warning("⚠️ Crie um roteiro na página anterior primeiro.")
    st.stop()

col_config, col_action = st.columns([1, 2])

with col_config:
    st.subheader("Configuração")
    preview = st.checkbox("Modo Preview (1 min)", value=True, help="Desmarque para gerar o vídeo completo (demora mais).")
    titulo_capa = st.text_input("Título na Capa", value="História Épica")

with col_action:
    st.subheader("Processamento")
    
    # Botão 1: Assets
    if st.button("1. Gerar Áudio e Capa"):
        with st.spinner("Gerando assets..."):
            # Gera Capa
            capa = utils.gerar_capa_simples(titulo_capa, "Canal IA")
            st.session_state['imagem_capa_path'] = capa
            st.image(capa, width=200, caption="Capa Gerada")
            
            # Gera Áudios
            utils.gerar_audio(st.session_state['texto_completo_en'], "en")
            utils.gerar_audio(st.session_state['texto_completo_pt'], "pt")
        st.success("Assets Prontos!")

    # Botão 2: Render
    if st.button("2. Renderizar Vídeos"):
        if not os.path.exists("temp/audio_pt.mp3"):
            st.error("Gere os áudios primeiro.")
        else:
            prog = st.progress(0)
            
            with st.spinner("Renderizando PT-BR..."):
                vid_pt = utils.renderizar_video("temp/audio_pt.mp3", st.session_state['imagem_capa_path'], "pt", preview)
                if vid_pt: st.video(vid_pt)
            
            prog.progress(50)
            
            with st.spinner("Renderizando English..."):
                vid_en = utils.renderizar_video("temp/audio_en.mp3", st.session_state['imagem_capa_path'], "en", preview)
                if vid_en: st.video(vid_en)
            
            prog.progress(100)
            st.balloons()
