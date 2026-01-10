import streamlit as st
import utils
import os

st.set_page_config(page_title="Estúdio", page_icon="🎬", layout="wide")

# --- 🔒 TRAVA DE SEGURANÇA (CORRIGIDA) ---
if not utils.verificar_senha():
    st.stop()
# -----------------------------------------

st.title("🎬 Estúdio de Produção")

# --- BLOCO DE SEGURANÇA ---
keys_necessarias = ['sinopse_en', 'titulos_en', 'texto_completo_en', 'texto_completo_pt', 'imagem_capa_path', 'tema_atual']
for k in keys_necessarias:
    if k not in st.session_state:
        st.session_state[k] = None

# Verifica roteiro
if not st.session_state['texto_completo_pt']:
    st.warning("⚠️ Nenhum roteiro encontrado na memória.")
    st.info("Por favor, vá para a página **Roteirização** primeiro para criar ou carregar uma história.")
    st.stop()

col_config, col_action = st.columns([1, 2])

with col_config:
    st.subheader("Configuração")
    preview = st.checkbox("Modo Preview (1 min)", value=True, help="Desmarque para gerar o vídeo completo (demora mais).")
    
    valor_padrao = "Minha História"
    if st.session_state.get('tema_atual'):
         valor_padrao = st.session_state['tema_atual']
         
    titulo_capa = st.text_input("Título na Capa", value=valor_padrao)

with col_action:
    st.subheader("Processamento")
    
    # --- BOTÃO 1: GERAR ASSETS ---
    if st.button("1. Gerar Áudio e Capa", type="primary"):
        with st.spinner("Gerando assets..."):
            # Gera Capa
            capa = utils.gerar_capa_simples(titulo_capa, "Canal IA")
            st.session_state['imagem_capa_path'] = capa
            
            # Gera Áudios (Passando o titulo para IA falar)
            if st.session_state['texto_completo_en']:
                utils.gerar_audio(st.session_state['texto_completo_en'], "en", titulo_capa)
            if st.session_state['texto_completo_pt']:
                utils.gerar_audio(st.session_state['texto_completo_pt'], "pt", titulo_capa)
        
        st.success("Assets Prontos! Ouça abaixo 👇")

    # --- PLAYERS DE ÁUDIO ---
    if os.path.exists("temp/audio_pt.mp3") and os.path.exists("temp/audio_en.mp3"):
        st.divider()
        col_audio1, col_audio2 = st.columns(2)
        
        with col_audio1:
            st.markdown("🎧 **Áudio Português**")
            st.audio("temp/audio_pt.mp3")
            
        with col_audio2:
            st.markdown("🎧 **Áudio Inglês**")
            st.audio("temp/audio_en.mp3")
            
        if os.path.exists("temp/capa_gerada.png"):
            st.image("temp/capa_gerada.png", width=150, caption="Capa Gerada")
        st.divider()

    # --- BOTÃO 2: RENDERIZAR ---
    if st.button("2. Renderizar Vídeos"):
        if not os.path.exists("temp/audio_pt.mp3"):
            st.error("Gere os áudios primeiro (Botão 1).")
        else:
            prog = st.progress(0)
            
            caminho_capa = st.session_state.get('imagem_capa_path')
            if not caminho_capa or not os.path.exists(caminho_capa):
                st.warning("Capa não encontrada, gerando uma nova rápida...")
                caminho_capa = utils.gerar_capa_simples(titulo_capa, "Auto")

            with st.spinner("Renderizando PT-BR..."):
                vid_pt = utils.renderizar_video("temp/audio_pt.mp3", caminho_capa, "pt", preview)
                if vid_pt: st.video(vid_pt)
            
            prog.progress(50)
            
            with st.spinner("Renderizando English..."):
                vid_en = utils.renderizar_video("temp/audio_en.mp3", caminho_capa, "en", preview)
                if vid_en: st.video(vid_en)
            
            prog.progress(100)
            st.balloons()
