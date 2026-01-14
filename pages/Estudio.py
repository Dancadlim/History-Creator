import streamlit as st
import utils
import agentes_producao
import os

# --- CORREÇÃO DE IMPORT (MOVIEPY v2) ---
try:
    from moviepy.audio.io.AudioFileClip import AudioFileClip
except ImportError:
    from moviepy.editor import AudioFileClip
# ---------------------------------------

st.set_page_config(page_title="Estúdio", page_icon="🎬", layout="wide")
if not utils.verificar_senha(): st.stop()

st.title("🎬 Estúdio de Produção")

# --- VALIDAÇÕES ---
if 'texto_completo_pt' not in st.session_state or not st.session_state['texto_completo_pt']:
    st.warning("⚠️ Nenhum roteiro carregado. Vá para a Biblioteca.")
    st.stop()

# Inicializa variáveis
if 'caminhos_imagens' not in st.session_state: st.session_state['caminhos_imagens'] = []
if 'caminhos_audio' not in st.session_state: st.session_state['caminhos_audio'] = {"pt": None, "en": None}
if 'prompts_usados_teste' not in st.session_state: st.session_state['prompts_usados_teste'] = []

# --- FUNÇÃO DE EXTRAÇÃO INTELIGENTE ---
def extrair_capitulo_1(texto_completo):
    if not texto_completo: return ""
    if '## ' in texto_completo:
        partes = texto_completo.split('## ')
        if len(partes) > 1:
            return "## " + partes[1]
    return texto_completo[:1500]

# --- INTERFACE ---
col_config, col_status = st.columns([1, 2])

with col_config:
    st.subheader("⚙️ Configuração")
    titulo_video = st.text_input("Título", value=st.session_state.get('tema_atual', 'História'))
    
    prompts_totais = st.session_state.get('prompts_visuais', [])
    st.metric("Cenas Totais", len(prompts_totais))
    
    st.divider()
    
    st.markdown("#### 🧪 Modo Teste (Capítulo 1)")
    modo_teste = st.checkbox("Ativar Modo Teste", value=True)
    if modo_teste:
        st.info("⚡ **Rápido:** Apenas Cap 1 (Texto) + 5 Imagens.")

with col_status:
    st.subheader("🏭 Linha de Produção")
    
    # 1. GERAR ASSETS
    if st.button("1. Gerar Áudios e Imagens", type="primary", use_container_width=True):
        if not prompts_totais:
            st.error("Sem prompts.")
        else:
            if modo_teste:
                prompts_para_usar = prompts_totais[:5]
                texto_pt = extrair_capitulo_1(st.session_state.get('texto_completo_pt', ''))
                texto_en = extrair_capitulo_1(st.session_state.get('texto_completo_en', ''))
                suffix = "_teste_v5"
            else:
                prompts_para_usar = prompts_totais
                texto_pt = st.session_state.get('texto_completo_pt', '')
                texto_en = st.session_state.get('texto_completo_en', '')
                suffix = ""
            
            st.session_state['prompts_usados_teste'] = prompts_para_usar

            with st.status("Produzindo...", expanded=True) as status:
                st.write(f"🎙️ Gravando Texto PT ({len(texto_pt)} chars)...")
                
                path_pt = agentes_producao.gerar_audio(texto_pt, "pt", titulo_video)
                st.session_state['caminhos_audio']['pt'] = path_pt
                
                if texto_en:
                    path_en = agentes_producao.gerar_audio(texto_en, "en", titulo_video)
                    st.session_state['caminhos_audio']['en'] = path_en
                
                st.write(f"🎨 Pintando {len(prompts_para_usar)} cenas...")
                lista_imgs = []
                prog = st.progress(0)
                for i, p in enumerate(prompts_para_usar):
                    path = agentes_producao.gerar_imagem_ia(p, f"cena_{i}_{str(hash(p))[:8]}{suffix}")
                    if path: lista_imgs.append(path)
                    prog.progress((i+1)/len(prompts_para_usar))
                
                st.session_state['caminhos_imagens'] = lista_imgs
                status.update(label="Assets Prontos!", state="complete")
                st.rerun()

    # PREVIEW
    if st.session_state['caminhos_audio']['pt']:
        st.audio(st.session_state['caminhos_audio']['pt'], format="audio/mp3")

    if st.session_state['caminhos_imagens']:
        with st.expander("👁️ Visualizar Imagens", expanded=False):
            imgs = st.session_state['caminhos_imagens']
            prms = st.session_state.get('prompts_usados_teste', [])
            cols = st.columns(3)
            for i, path in enumerate(imgs):
                with cols[i%3]:
                    st.image(path, use_container_width=True)
                    if i < len(prms):
                        st.caption(f"{prms[i][:60]}...")

    st.divider()
    
    # 2. RENDERIZAR
    col_pt, col_en = st.columns(2)
    
    with col_pt:
        path_audio = st.session_state['caminhos_audio']['pt']
        if st.button("2. Renderizar PT", disabled=not path_audio):
            with st.spinner("Renderizando..."):
                try:
                    if not st.session_state['caminhos_imagens']:
                        st.error("Sem imagens!")
                    else:
                        # Se for teste, cortamos áudio manualmente aqui
                        audio_final = path_audio
                        if modo_teste:
                             try:
                                clip = AudioFileClip(path_audio)
                                duracao = min(len(st.session_state['caminhos_imagens']) * 6, clip.duration)
                                # Em MoviePy v2 pode ser .with_duration ou subclipped
                                # Tentando subclip padrão
                                clip = clip.subclip(0, duracao)
                                audio_final = "temp/audio_teste_cortado.mp3"
                                clip.write_audiofile(audio_final)
                             except Exception as e:
                                st.warning(f"Não foi possível cortar áudio (usando completo): {e}")

                        v_pt = agentes_producao.renderizar_video_com_imagens(
                            audio_final, 
                            st.session_state['caminhos_imagens'], 
                            "pt"
                        )
                        if v_pt:
                            st.success("Sucesso!")
                            st.video(v_pt)
                            with open(v_pt, "rb") as f: st.download_button("⬇️ Baixar", f, "video_teste.mp4")
                        else:
                            st.error("Renderizador retornou None.")
                except Exception as e:
                    st.error(f"ERRO FATAL: {e}")
