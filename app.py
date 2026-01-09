# Arquivo: app.py
import streamlit as st
import utils  # Importa o arquivo acima
import os

st.set_page_config(page_title="Content Farm IA", page_icon="🏭", layout="wide")

st.title("🏭 Central de Produção de Conteúdo")
st.markdown("""
### Bem-vindo ao seu Estúdio de IA

O sistema está dividido em páginas para organizar o fluxo (veja o menu lateral 👈):

1.  **1_✍️_Roteirizacao**: Aqui criamos a história, estruturamos os capítulos e traduzimos.
2.  **2_🎬_Estudio**: Aqui pegamos o roteiro pronto e geramos áudio e vídeo.
""")

# --- SETUP INICIAL ---
# Conecta a API usando a função que criamos no utils.py
if utils.setup_api():
    st.success("✅ API do Google Conectada e Pronta!")
else:
    st.error("⚠️ API não configurada no secrets.toml")

# --- MEMÓRIA DA SESSÃO ---
# Isso garante que o roteiro não suma quando você mudar de página
session_keys = ['sinopse_en', 'titulos_en', 'texto_completo_en', 'texto_completo_pt', 'imagem_capa_path']

for k in session_keys:
    if k not in st.session_state:
        st.session_state[k] = None

st.divider()

# Status rápido
if st.session_state['texto_completo_pt']:
    st.info("🔥 Existe um roteiro carregado na memória pronto para virar vídeo!")
    st.write(f"**Tamanho do Texto:** {len(st.session_state['texto_completo_pt'])} caracteres")
else:
    st.warning("💤 Nenhum roteiro na memória. Vá para a página de Roteirização para começar.")
