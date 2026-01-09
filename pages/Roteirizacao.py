import streamlit as st
import utils
import time

st.set_page_config(page_title="Roteiro", page_icon="✍️", layout="wide")
st.title("✍️ Roteirista (English First)")

col1, col2 = st.columns(2)
with col1:
    nicho = st.selectbox("Nicho", ["Bible Stories", "Mystery", "History", "Curiosities"])
with col2:
    tema = st.text_input("Tema da História")

if st.button("🚀 Iniciar Criação"):
    if not tema:
        st.warning("Escreva um tema.")
    else:
        with st.status("Escrevendo história...", expanded=True) as status:
            st.write("Criando Sinopse...")
            sinopse = utils.agente_sinopse(tema, nicho)
            st.session_state['sinopse_en'] = sinopse
            
            st.write("Estruturando Capítulos...")
            titulos = utils.agente_titulos(sinopse)
            
            st.write("Escrevendo Texto Completo (Aguarde)...")
            texto_full = ""
            progresso = st.progress(0)
            
            for i, t in enumerate(titulos):
                if t.strip():
                    cap = utils.agente_escreve_capitulo(t, sinopse, texto_full)
                    texto_full += f"\n\n## {t}\n\n{cap}"
                    progresso.progress((i+1)/len(titulos))
                    time.sleep(1) # Evita erro de limite da API
            
            st.session_state['texto_completo_en'] = texto_full
            
            st.write("Traduzindo para Português...")
            st.session_state['texto_completo_pt'] = utils.agente_tradutor(texto_full)
            
            status.update(label="Concluído!", state="complete", expanded=False)
            st.success("História pronta!")

if st.session_state['texto_completo_pt']:
    tab_pt, tab_en = st.tabs(["🇧🇷 Português", "🇺🇸 English"])
    with tab_pt:
        st.text_area("Roteiro PT", st.session_state['texto_completo_pt'], height=400)
    with tab_en:
        st.text_area("Roteiro EN", st.session_state['texto_completo_en'], height=400)
