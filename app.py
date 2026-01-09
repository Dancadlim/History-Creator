import streamlit as st
import utils
import os

st.set_page_config(page_title="Content Farm IA", page_icon="🏭", layout="wide")

st.title("🏭 Central de Produção de Conteúdo")
st.markdown("""
Bem-vindo ao seu Estúdio de IA. Utilize o menu lateral para navegar:

1.  **Roteirização**: Criação da história (EN -> PT).
2.  **Estúdio**: Geração de Áudio e Vídeo.
""")

# Setup Inicial
if utils.setup_api():
    st.success("✅ API Conectada")
else:
    st.error("⚠️ Configure o secrets.toml")

# Inicializa variáveis globais de sessão
session_keys = ['sinopse_en', 'titulos_en', 'texto_completo_en', 'texto_completo_pt', 'imagem_capa_path']
for k in session_keys:
    if k not in st.session_state:
        st.session_state[k] = None

st.divider()

if st.session_state['texto_completo_pt']:
    st.info("🔥 Roteiro carregado na memória! Vá para a página **Estúdio**.")
