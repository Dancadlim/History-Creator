import streamlit as st
import utils
import agentes_producao
import os

st.set_page_config(page_title="Estúdio", page_icon="🎬", layout="wide")
if not utils.verificar_senha(): st.stop()

st.title("🎬 Estúdio de Produção")

if 'texto_completo_pt' not in st.session_state or not st.session_state['texto_completo_pt']:
    st.warning("⚠️ Nenhum roteiro carregado. Vá para a Biblioteca.")
    st.stop()

if 'caminhos_imagens' not in st.session_state: st.session_state['caminhos_imagens'] = []
if 'caminhos_audio' not in st.session_state: st.session_state['caminhos_audio'] = {"pt": None, "en": None}

col_config, col_status = st.columns([1, 2])

with col_config:
    st.subheader("⚙️ Config")
    titulo_video = st.text_input("Título", value=st.session_state.get('tema_atual', 'História'))
    prompts = st.session_state.get('prompts_visuais', [])
    st.metric("Cenas", len(prompts))
    st.caption("Modelo de Imagem: **Imagen 4 Fast (16:9)**")

with col_status:
    st.subheader("🏭 Linha de Produção")
    
    if st.button("1. Gerar Áudios e Imagens", type="primary", use_container_width=True):
        if not prompts:
            st.error("Sem prompts.")
        else:
            with st.status("Gerando Assets...", expanded=True) as status:
                # Áudios
                st.write("🎙️ TTS...")
                st.session_state['caminhos_audio']['pt'] = agentes_producao.gerar_audio(st.session_state['texto_completo_pt'], "pt", titulo_video)
                st.session_state['caminhos_audio']['en'] = agentes_producao.gerar_audio(st.session_state['texto_completo_en'], "en", titulo_video)
                
                # Imagens
                st.write(f"🎨 Pintando {len(prompts)} cenas (Imagen 4 Fast)...")
                lista_imgs = []
                prog = st.progress(0)
                for i, p in enumerate(prompts):
                    safe_name = f"cena_{i}_{str(hash(p))[:8]}"
                    # Chama a função nova do agentes_producao
                    path = agentes_producao.gerar_imagem_ia(p, safe_name)
                    if path: lista_imgs.append(path)
                    prog.progress((i+1)/len(prompts))
                
                st.session_state['caminhos_imagens'] = lista_imgs
                status.update(label="Pronto!", state="complete")
                st.rerun()

    if st.session_state['caminhos_imagens']:
        with st.expander("Preview Imagens", expanded=False):
            st.image(st.session_state['caminhos_imagens'][:4], width=150, caption="Amostra")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("2. Renderizar PT-BR", disabled=not st.session_state['caminhos_audio']['pt']):
            with st.spinner("Renderizando..."):
                v_pt = agentes_producao.renderizar_video_com_imagens(st.session_state['caminhos_audio']['pt'], st.session_state['caminhos_imagens'], "pt")
                if v_pt:
                    st.video(v_pt)
                    with open(v_pt, "rb") as f: st.download_button("⬇️ Baixar PT", f, "video_pt.mp4")

    with c2:
        if st.button("2. Renderizar EN", disabled=not st.session_state['caminhos_audio']['en']):
            with st.spinner("Rendering..."):
                v_en = agentes_producao.renderizar_video_com_imagens(st.session_state['caminhos_audio']['en'], st.session_state['caminhos_imagens'], "en")
                if v_en:
                    st.video(v_en)
                    with open(v_en, "rb") as f: st.download_button("⬇️ Download EN", f, "video_en.mp4")
