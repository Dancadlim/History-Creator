import streamlit as st
import utils
import agentes_producao  # A nova fábrica
import os

st.set_page_config(page_title="Estúdio", page_icon="🎬", layout="wide")

# --- 🔒 TRAVA DE SEGURANÇA ---
if not utils.verificar_senha():
    st.stop()

st.title("🎬 Estúdio de Produção")

# --- VERIFICAÇÃO DE MEMÓRIA ---
# Garante que temos uma história carregada para produzir
if 'texto_completo_pt' not in st.session_state or not st.session_state['texto_completo_pt']:
    st.warning("⚠️ Nenhum roteiro carregado.")
    st.info("Vá para **Roteirização** (criar novo) ou **Biblioteca** (carregar existente).")
    st.stop()

# Inicializa variáveis de caminhos se não existirem
if 'caminhos_imagens' not in st.session_state:
    st.session_state['caminhos_imagens'] = []
if 'caminhos_audio' not in st.session_state:
    st.session_state['caminhos_audio'] = {"pt": None, "en": None}

# --- CONFIGURAÇÃO ---
col_config, col_status = st.columns([1, 2])

with col_config:
    st.subheader("⚙️ Config")
    titulo_video = st.text_input("Título do Vídeo", value=st.session_state.get('tema_atual', 'Minha História'))
    
    # Mostra quantos prompts temos
    prompts = st.session_state.get('prompts_visuais', [])
    st.metric("Cenas (Prompts)", len(prompts))
    
    if not prompts:
        st.error("ERRO: Roteiro sem prompts visuais. A IA não gerou as descrições das cenas.")

with col_status:
    st.subheader("🏭 Linha de Produção")
    
    # --- PASSO 1: GERAR ASSETS (ÁUDIO + IMAGENS) ---
    if st.button("1. Gerar Áudios e Imagens", type="primary", use_container_width=True):
        if not prompts:
            st.error("Não há prompts para gerar imagens.")
        else:
            with st.status("Trabalhando nos Assets...", expanded=True) as status:
                
                # A. ÁUDIOS
                st.write("🎙️ Gerando Narração (TTS)...")
                if st.session_state.get('texto_completo_pt'):
                    path_pt = agentes_producao.gerar_audio(st.session_state['texto_completo_pt'], "pt", titulo_video)
                    st.session_state['caminhos_audio']['pt'] = path_pt
                
                if st.session_state.get('texto_completo_en'):
                    path_en = agentes_producao.gerar_audio(st.session_state['texto_completo_en'], "en", titulo_video)
                    st.session_state['caminhos_audio']['en'] = path_en
                
                # B. IMAGENS (LOOP)
                st.write(f"🎨 Pintando {len(prompts)} cenas com IA...")
                lista_imgs = []
                progresso = st.progress(0)
                
                for i, prompt in enumerate(prompts):
                    # Nome único para cada imagem: historia_X_cena_Y.png
                    # Usamos um hash simples do prompt ou index para garantir ordem
                    safe_name = f"cena_{i}_{str(hash(prompt))[:8]}"
                    
                    caminho_img = agentes_producao.gerar_imagem_ia(prompt, safe_name)
                    if caminho_img:
                        lista_imgs.append(caminho_img)
                    
                    progresso.progress((i + 1) / len(prompts))
                
                st.session_state['caminhos_imagens'] = lista_imgs
                status.update(label="Assets Gerados com Sucesso!", state="complete", expanded=False)
                st.rerun()

    # --- PREVIEW DOS ASSETS ---
    if st.session_state['caminhos_imagens']:
        with st.expander("Ver Imagens Geradas", expanded=False):
            st.image(st.session_state['caminhos_imagens'], width=150, caption=[f"Cena {i+1}" for i in range(len(st.session_state['caminhos_imagens']))])

    if st.session_state['caminhos_audio']['pt']:
        st.audio(st.session_state['caminhos_audio']['pt'], format="audio/mp3")

    # --- PASSO 2: RENDERIZAR VÍDEO ---
    st.divider()
    col_render_pt, col_render_en = st.columns(2)
    
    with col_render_pt:
        if st.button("2. Renderizar Vídeo PT-BR", disabled=not st.session_state['caminhos_audio']['pt']):
            with st.spinner("Editando vídeo PT..."):
                video_pt = agentes_producao.renderizar_video_com_imagens(
                    st.session_state['caminhos_audio']['pt'],
                    st.session_state['caminhos_imagens'],
                    "pt"
                )
                if video_pt:
                    st.video(video_pt)
                    st.success("Vídeo PT Pronto!")
                    
                    # Botão de Download
                    with open(video_pt, "rb") as file:
                        st.download_button("⬇️ Baixar MP4 (PT)", data=file, file_name="historia_pt.mp4", mime="video/mp4")

    with col_render_en:
        if st.button("2. Renderizar Vídeo EN", disabled=not st.session_state['caminhos_audio']['en']):
            with st.spinner("Editando vídeo EN..."):
                video_en = agentes_producao.renderizar_video_com_imagens(
                    st.session_state['caminhos_audio']['en'],
                    st.session_state['caminhos_imagens'],
                    "en"
                )
                if video_en:
                    st.video(video_en)
                    st.success("Video EN Ready!")
                    
                    with open(video_en, "rb") as file:
                        st.download_button("⬇️ Download MP4 (EN)", data=file, file_name="story_en.mp4", mime="video/mp4")
