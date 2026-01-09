# Arquivo: pages/1_✍️_Roteirizacao.py
import streamlit as st
import utils
import time

st.set_page_config(page_title="Roteirização", page_icon="✍️", layout="wide")
st.title("✍️ Agente Roteirista (English First)")

col1, col2 = st.columns(2)
with col1:
    nicho = st.selectbox("Nicho", ["Bible Stories", "Mystery", "History", "Curiosities"])
with col2:
    tema = st.text_input("Tema da História")

if st.button("🚀 Iniciar Criação"):
    if not tema:
        st.error("Defina um tema.")
    else:
        # 1. Sinopse
        with st.status("Planejando História...", expanded=True) as status:
            st.write("Gerando Sinopse em Inglês...")
            sinopse = utils.agente_sinopse(tema, nicho)
            st.session_state['sinopse_en'] = sinopse
            
            st.write("Estruturando Capítulos...")
            titulos = utils.agente_titulos(sinopse)
            st.session_state['titulos_en'] = titulos
            
            st.write("Escrevendo Capítulos (Isso demora um pouco)...")
            texto_full = ""
            progresso = st.progress(0)
            
            for i, t in enumerate(titulos):
                if t.strip():
                    cap = utils.agente_escreve_capitulo(t, sinopse, texto_full)
                    texto_full += f"\n\n## {t}\n\n{cap}"
                    progresso.progress((i+1)/len(titulos))
                    time.sleep(1)
            
            st.session_state['texto_completo_en'] = texto_full
            
            st.write("Traduzindo para Português...")
            st.session_state['texto_completo_pt'] = utils.agente_tradutor(texto_full)
            
            status.update(label="Processo Concluído!", state="complete", expanded=False)
            st.success("História pronta! Verifique abaixo.")

# Exibição dos Resultados
if st.session_state['texto_completo_en']:
    tab_en, tab_pt = st.tabs(["🇺🇸 English", "🇧🇷 Português"])
    with tab_en:
        st.text_area("Roteiro EN", st.session_state['texto_completo_en'], height=400)
    with tab_pt:
        st.text_area("Roteiro PT", st.session_state['texto_completo_pt'], height=400)
