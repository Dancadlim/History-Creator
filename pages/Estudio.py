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

# Inicializa listas se não existirem
if 'caminhos_imagens' not in st.session_state: st.session_state['caminhos_imagens'] = []
if 'caminhos_audio' not in st.session_state: st.session_state['caminhos_audio'] = {"pt": None, "en": None}

col_config, col_status = st.columns([1, 2])

with col_config:
    st.subheader("⚙️ Configuração")
    titulo_video = st.text_input("Título", value=st.session_state.get('tema_atual', 'História'))
    
    prompts_totais = st.session_state.get('prompts_visuais', [])
    st.metric("Cenas Totais no Roteiro", len(prompts_totais))
    
    st.divider()
    
    # --- MODO TESTE (ECONOMIA) ---
    st.markdown("#### 🧪 Controle de Custo")
    modo_teste = st.checkbox("Ativar Modo Teste (Gera apenas 5 cenas)", value=True, help="Ideal para validar áudio/vídeo sem gastar muitos créditos.")
    
    if modo_teste:
        st.info(f"Serão geradas apenas 5 imagens (Custo est: ~$0.10)")
    else:
        st.warning(f"Serão geradas TODAS as {len(prompts_totais)} imagens. (Custo maior)")
        
    st.caption("Modelo: **Imagen 4 Fast (16:9)**")

with col_status:
    st.subheader("🏭 Linha de Produção")
    
    if st.button("1. Gerar Áudios e Imagens", type="primary", use_container_width=True):
        if not prompts_totais:
            st.error("Sem prompts no roteiro.")
        else:
            # DEFINE QUANTOS PROMPTS USAR
            prompts_para_usar = prompts_totais[:5] if modo_teste else prompts_totais
            
            with st.status("Gerando Assets...", expanded=True) as status:
                # 1. Áudios (Gera tudo para garantir coerência, áudio é barato/grátis)
                st.write("🎙️ Gerando Narração (TTS)...")
                if st.session_state.get('texto_completo_pt'):
                    path_pt = agentes_producao.gerar_audio(st.session_state['texto_completo_pt'], "pt", titulo_video)
                    st.session_state['caminhos_audio']['pt'] = path_pt
                
                if st.session_state.get('texto_completo_en'):
                    path_en = agentes_producao.gerar_audio(st.session_state['texto_completo_en'], "en", titulo_video)
                    st.session_state['caminhos_audio']['en'] = path_en
                
                # 2. Imagens
                st.write(f"🎨 Pintando {len(prompts_para_usar)} cenas com Imagen 4 Fast...")
                lista_imgs = []
                prog = st.progress(0)
                
                for i, p in enumerate(prompts_para_usar):
                    # Hash curto para garantir nome de arquivo único
                    safe_name = f"cena_{i}_{str(hash(p))[:8]}"
                    if modo_teste: safe_name += "_teste"
                    
                    path = agentes_producao.gerar_imagem_ia(p, safe_name)
                    if path: lista_imgs.append(path)
                    
                    prog.progress((i+1)/len(prompts_para_usar))
                
                st.session_state['caminhos_imagens'] = lista_imgs
                status.update(label="Assets Prontos!", state="complete")
                
                # Aviso se o áudio inglês falhou
                if not st.session_state['caminhos_audio']['en']:
                    st.warning("⚠️ Áudio em Inglês não foi gerado (texto vazio?).")
                
                st.rerun()

    # Preview
    if st.session_state['caminhos_imagens']:
        with st.expander(f"Ver {len(st.session_state['caminhos_imagens'])} Imagens Geradas", expanded=False):
            st.image(st.session_state['caminhos_imagens'][:4], width=150)

    st.divider()
    
    # Renderização
    c1, c2 = st.columns(2)
    with c1:
        # Só habilita se tiver áudio PT
        tem_audio_pt = st.session_state['caminhos_audio']['pt'] is not None
        if st.button("2. Renderizar PT-BR", disabled=not tem_audio_pt):
            with st.spinner("Renderizando Vídeo PT..."):
                # Se for modo teste, cortamos o áudio para bater com as 5 imagens (opcional, ou deixamos esticado)
                # O ideal no renderizador simples: ele divide o tempo total do áudio pelo numero de imagens.
                # Se tiver 30 min de áudio e 5 imagens, cada imagem vai durar 6 minutos. Para teste visual ok.
                v_pt = agentes_producao.renderizar_video_com_imagens(
                    st.session_state['caminhos_audio']['pt'], 
                    st.session_state['caminhos_imagens'], 
                    "pt"
                )
                if v_pt:
                    st.video(v_pt)
                    with open(v_pt, "rb") as f: st.download_button("⬇️ Baixar PT", f, "video_pt.mp4")

    with c2:
        # Só habilita se tiver áudio EN
        tem_audio_en = st.session_state['caminhos_audio']['en'] is not None
        if st.button("2. Renderizar EN", disabled=not tem_audio_en):
            with st.spinner("Renderizando Vídeo EN..."):
                v_en = agentes_producao.renderizar_video_com_imagens(
                    st.session_state['caminhos_audio']['en'], 
                    st.session_state['caminhos_imagens'], 
                    "en"
                )
                if v_en:
                    st.video(v_en)
                    with open(v_en, "rb") as f: st.download_button("⬇️ Baixar EN", f, "video_en.mp4")
