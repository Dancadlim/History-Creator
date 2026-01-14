import streamlit as st
import utils
import agentes_producao
import os

st.set_page_config(page_title="Estúdio", page_icon="🎬", layout="wide")
if not utils.verificar_senha(): st.stop()

st.title("🎬 Estúdio de Produção")

# --- VALIDAÇÕES INICIAIS ---
if 'texto_completo_pt' not in st.session_state or not st.session_state['texto_completo_pt']:
    st.warning("⚠️ Nenhum roteiro carregado. Vá para a Biblioteca.")
    st.stop()

# Inicializa variáveis
if 'caminhos_imagens' not in st.session_state: st.session_state['caminhos_imagens'] = []
if 'prompts_usados_teste' not in st.session_state: st.session_state['prompts_usados_teste'] = [] 
if 'caminhos_audio' not in st.session_state: st.session_state['caminhos_audio'] = {"pt": None, "en": None}
if 'texto_narrado_teste' not in st.session_state: st.session_state['texto_narrado_teste'] = "" # Debug

# --- FUNÇÃO AUXILIAR: EXTRAIR CAPÍTULO 1 ROBUSTA ---
def extrair_capitulo_1(texto_completo):
    """
    Tenta isolar apenas o primeiro capítulo.
    """
    if not texto_completo: return ""
    
    # 1. Tenta dividir pelo marcador padrão Markdown '## '
    partes = texto_completo.split('## ')
    if len(partes) > 2:
        # partes[0] = vazio/intro, partes[1] = Titulo, partes[2] = Cap 1
        return "## " + partes[2] 
    elif len(partes) > 1:
        # Caso só tenha Titulo e Cap 1
        return "## " + partes[1]
    
    # 2. Se falhar, pega os primeiros 1000 caracteres (Fallback)
    return texto_completo[:1000] + "..."

# --- INTERFACE ---
col_config, col_status = st.columns([1, 2])

with col_config:
    st.subheader("⚙️ Configuração")
    titulo_video = st.text_input("Título", value=st.session_state.get('tema_atual', 'História'))
    
    prompts_totais = st.session_state.get('prompts_visuais', [])
    st.metric("Cenas Totais", len(prompts_totais))
    
    st.divider()
    
    # --- MODO TESTE ---
    st.markdown("#### 🧪 Modo Teste (Capítulo 1)")
    modo_teste = st.checkbox("Ativar Modo Teste", value=True)
    
    if modo_teste:
        st.info("⚡ **Modo Rápido:**\n- Gera áudio só do Cap 1.\n- Gera só 5 imagens.")
    else:
        st.warning("🚨 **Modo Completo:**\n- Gera TUDO.\n- Pode demorar.")

with col_status:
    st.subheader("🏭 Linha de Produção")
    
    # BOTÃO 1: GERAR ASSETS
    if st.button("1. Gerar Áudios e Imagens", type="primary", use_container_width=True):
        if not prompts_totais:
            st.error("Sem prompts no roteiro.")
        else:
            # --- DEFINIÇÃO DO ESCOPO ---
            if modo_teste:
                prompts_para_usar = prompts_totais[:5]
                # Usa a função robusta para extrair texto
                texto_pt_uso = extrair_capitulo_1(st.session_state.get('texto_completo_pt', ''))
                texto_en_uso = extrair_capitulo_1(st.session_state.get('texto_completo_en', ''))
                suffix_nome = "_teste_v3" # v3 para limpar cache antigo
            else:
                prompts_para_usar = prompts_totais
                texto_pt_uso = st.session_state.get('texto_completo_pt', '')
                texto_en_uso = st.session_state.get('texto_completo_en', '')
                suffix_nome = ""

            # Salva para debug visual
            st.session_state['prompts_usados_teste'] = prompts_para_usar
            st.session_state['texto_narrado_teste'] = texto_pt_uso
            
            with st.status("Produzindo Assets...", expanded=True) as status:
                
                # A. ÁUDIOS
                st.write("🎙️ Gravando Narração...")
                
                if texto_pt_uso:
                    path_pt = agentes_producao.gerar_audio(texto_pt_uso, "pt", titulo_video)
                    if path_pt and os.path.exists(path_pt):
                        st.session_state['caminhos_audio']['pt'] = path_pt
                    else:
                        st.error("Falha ao criar arquivo de áudio PT.")
                
                if texto_en_uso:
                    path_en = agentes_producao.gerar_audio(texto_en_uso, "en", titulo_video)
                    st.session_state['caminhos_audio']['en'] = path_en
                
                # B. IMAGENS
                st.write(f"🎨 Pintando {len(prompts_para_usar)} cenas...")
                lista_imgs = []
                prog = st.progress(0)
                
                for i, p in enumerate(prompts_para_usar):
                    safe_name = f"cena_{i}_{str(hash(p))[:8]}{suffix_nome}"
                    path = agentes_producao.gerar_imagem_ia(p, safe_name)
                    if path: lista_imgs.append(path)
                    prog.progress((i+1)/len(prompts_para_usar))
                
                st.session_state['caminhos_imagens'] = lista_imgs
                status.update(label="Assets Prontos!", state="complete")
                st.rerun()

    # --- ÁREA DE DIAGNÓSTICO E PREVIEW (CORRIGIDA) ---
    
    # 1. Debug do Texto (Para ver se o Capítulo 1 foi extraído certo)
    if st.session_state.get('texto_narrado_teste'):
        with st.expander("📝 Texto enviado para Narração (Debug)", expanded=False):
            st.text(st.session_state['texto_narrado_teste'])
            if len(st.session_state['texto_narrado_teste']) < 10:
                st.error("⚠️ O texto parece muito curto ou vazio! Isso explica o erro no vídeo.")

    # 2. Player de Áudio (AGORA DE VOLTA!)
    if st.session_state['caminhos_audio']['pt']:
        st.write("🎧 **Áudio PT-BR Gerado:**")
        st.audio(st.session_state['caminhos_audio']['pt'], format="audio/mp3")
    else:
        if st.session_state.get('caminhos_imagens'): # Se tem imagens mas não áudio
            st.warning("⚠️ Áudio PT não encontrado. Tente gerar novamente.")

    # 3. Preview Imagens
    if st.session_state['caminhos_imagens']:
        with st.expander(f"👁️ Visualizar {len(st.session_state['caminhos_imagens'])} Imagens", expanded=False):
            st.image(st.session_state['caminhos_imagens'][:5], width=150)

    st.divider()
    
    # --- RENDERIZAÇÃO ---
    c1, c2 = st.columns(2)
    
    with c1:
        # Verifica se arquivo existe fisicamente
        audio_pt_path = st.session_state['caminhos_audio']['pt']
        tem_audio_pt = audio_pt_path is not None and os.path.exists(audio_pt_path)
        
        if st.button("2. Renderizar Vídeo (PT-BR)", disabled=not tem_audio_pt):
            with st.spinner("Editando vídeo PT..."):
                # Debug Check
                if not st.session_state['caminhos_imagens']:
                    st.error("Lista de imagens vazia.")
                else:
                    v_pt = agentes_producao.renderizar_video_com_imagens(
                        audio_pt_path, 
                        st.session_state['caminhos_imagens'], 
                        "pt"
                    )
                    
                    if v_pt:
                        st.success("Vídeo Renderizado!")
                        st.video(v_pt)
                        with open(v_pt, "rb") as f: st.download_button("⬇️ Baixar PT", f, "video_cap1_pt.mp4")
                    else:
                        st.error("Falha na renderização. Verifique os logs do terminal.")

    with c2:
        audio_en_path = st.session_state['caminhos_audio']['en']
        tem_audio_en = audio_en_path is not None and os.path.exists(audio_en_path)
        
        if st.button("2. Renderizar Vídeo (EN)", disabled=not tem_audio_en):
            with st.spinner("Editing EN video..."):
                v_en = agentes_producao.renderizar_video_com_imagens(
                    audio_en_path, 
                    st.session_state['caminhos_imagens'], 
                    "en"
                )
                if v_en:
                    st.video(v_en)
                    with open(v_en, "rb") as f: st.download_button("⬇️ Download EN", f, "video_cap1_en.mp4")
