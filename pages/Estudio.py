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

# --- FUNÇÃO AUXILIAR: EXTRAIR CAPÍTULO 1 ---
def extrair_capitulo_1(texto_completo):
    """
    Tenta isolar apenas o primeiro capítulo baseado nos marcadores Markdown '## '.
    """
    if not texto_completo: return ""
    
    # Divide pelos cabeçalhos de capítulo
    partes = texto_completo.split('## ')
    
    # partes[0] geralmente é vazio ou introdução. partes[1] é o Cap 1.
    if len(partes) > 1:
        # Reconstrói o título + texto do Cap 1
        return "## " + partes[1]
    
    # Fallback: Se não achar divisão, pega os primeiros 1500 caracteres
    return texto_completo[:1500]

# --- INTERFACE ---
col_config, col_status = st.columns([1, 2])

with col_config:
    st.subheader("⚙️ Configuração")
    titulo_video = st.text_input("Título", value=st.session_state.get('tema_atual', 'História'))
    
    prompts_totais = st.session_state.get('prompts_visuais', [])
    st.metric("Cenas Totais no Roteiro", len(prompts_totais))
    
    st.divider()
    
    # --- MODO TESTE ---
    st.markdown("#### 🧪 Modo Teste (Capítulo 1)")
    modo_teste = st.checkbox("Ativar Modo Teste", value=True)
    
    if modo_teste:
        st.info("⚡ GERAÇÃO RÁPIDA (Capítulo 1):\n- Apenas 5 Imagens.\n- Áudio apenas do 1º Capítulo.\n- Perfeito para validar a sincronia.")
    else:
        st.warning(f"🚨 MODO PRODUÇÃO COMPLETA:\n- Todas as {len(prompts_totais)} imagens.\n- História completa.\n- Renderização demorada.")

with col_status:
    st.subheader("🏭 Linha de Produção")
    
    # BOTÃO 1: GERAR ASSETS
    if st.button("1. Gerar Áudios e Imagens", type="primary", use_container_width=True):
        if not prompts_totais:
            st.error("Sem prompts no roteiro.")
        else:
            # --- DEFINIÇÃO DO ESCOPO (TESTE vs FULL) ---
            if modo_teste:
                # Pega só os 5 primeiros prompts (Cap 1)
                prompts_para_usar = prompts_totais[:5]
                # Corta o texto para ser só o Cap 1
                texto_pt_uso = extrair_capitulo_1(st.session_state.get('texto_completo_pt', ''))
                texto_en_uso = extrair_capitulo_1(st.session_state.get('texto_completo_en', ''))
                suffix_nome = "_teste_cap1"
            else:
                prompts_para_usar = prompts_totais
                texto_pt_uso = st.session_state.get('texto_completo_pt', '')
                texto_en_uso = st.session_state.get('texto_completo_en', '')
                suffix_nome = ""

            st.session_state['prompts_usados_teste'] = prompts_para_usar
            
            with st.status("Produzindo Assets...", expanded=True) as status:
                
                # A. ÁUDIOS (Gera só o trecho selecionado)
                st.write("🎙️ Gravando Narração...")
                
                if texto_pt_uso:
                    path_pt = agentes_producao.gerar_audio(texto_pt_uso, "pt", titulo_video)
                    st.session_state['caminhos_audio']['pt'] = path_pt
                
                if texto_en_uso:
                    path_en = agentes_producao.gerar_audio(texto_en_uso, "en", titulo_video)
                    st.session_state['caminhos_audio']['en'] = path_en
                
                # B. IMAGENS
                st.write(f"🎨 Pintando {len(prompts_para_usar)} cenas (Imagen 4 Fast)...")
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

    # PREVIEW COM CONTEXTO
    if st.session_state['caminhos_imagens']:
        with st.expander(f"👁️ Visualizar Assets ({len(st.session_state['caminhos_imagens'])} cenas)", expanded=True):
            imgs = st.session_state['caminhos_imagens']
            prms = st.session_state.get('prompts_usados_teste', [])
            
            cols = st.columns(3)
            for i, img_path in enumerate(imgs):
                with cols[i % 3]:
                    st.image(img_path, use_container_width=True)
                    caption = prms[i] if i < len(prms) else "..."
                    st.caption(f"**Cena {i+1}:** {caption[:80]}...")

    st.divider()
    
    # BOTÕES DE RENDERIZAÇÃO
    c1, c2 = st.columns(2)
    
    with c1:
        tem_audio_pt = st.session_state['caminhos_audio']['pt'] is not None
        if st.button("2. Renderizar Vídeo (PT-BR)", disabled=not tem_audio_pt):
            with st.spinner("Editando vídeo PT..."):
                # Como já geramos o áudio do tamanho certo (Cap 1), não precisa cortar nada.
                # O renderizador vai distribuir as 5 imagens ao longo do áudio do Cap 1.
                v_pt = agentes_producao.renderizar_video_com_imagens(
                    st.session_state['caminhos_audio']['pt'], 
                    st.session_state['caminhos_imagens'], 
                    "pt"
                )
                if v_pt:
                    st.video(v_pt)
                    with open(v_pt, "rb") as f: st.download_button("⬇️ Baixar PT", f, "video_cap1_pt.mp4")

    with c2:
        tem_audio_en = st.session_state['caminhos_audio']['en'] is not None
        if st.button("2. Renderizar Vídeo (EN)", disabled=not tem_audio_en):
            with st.spinner("Editing EN video..."):
                v_en = agentes_producao.renderizar_video_com_imagens(
                    st.session_state['caminhos_audio']['en'], 
                    st.session_state['caminhos_imagens'], 
                    "en"
                )
                if v_en:
                    st.video(v_en)
                    with open(v_en, "rb") as f: st.download_button("⬇️ Download EN", f, "video_cap1_en.mp4")
