import streamlit as st
import utils

st.set_page_config(page_title="Content Farm IA", page_icon="🏭", layout="wide")

# --- 🔒 TRAVA DE SEGURANÇA ---
if not utils.verificar_senha():
    st.stop()
# -----------------------------

st.title("🏭 Central de Produção de Conteúdo")
st.markdown("### v2.0 - Engine Híbrida (Imagen 4 Fast + Agentes Críticos)")

st.info("""
**Novidades desta versão:**
* 🎨 **Imagens:** Integração nativa com **Imagen 4 Fast** (Econômico e Realista).
* 🕵️ **Qualidade:** Novo Agente Crítico e Reescrita Automática.
* 📺 **Formato:** Vídeos padronizados em **16:9 (Cinematográfico)** com Zoom (Ken Burns).
""")

col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        st.subheader("1. Roteirização")
        st.write("Crie histórias com loop de feedback e crítica automática.")
        st.page_link("pages/1_Roteirizacao.py", label="Ir para Criação", icon="✍️")

with col2:
    with st.container(border=True):
        st.subheader("2. Estúdio")
        st.write("Gere áudios e vídeos usando a nova engine visual.")
        st.page_link("pages/2_Estudio.py", label="Ir para Produção", icon="🎬")

with col3:
    with st.container(border=True):
        st.subheader("3. Biblioteca")
        st.write("Gerencie roteiros, status e banco de dados.")
        st.page_link("pages/3_📚_Biblioteca.py", label="Ir para Arquivos", icon="📚")

# Setup Inicial (Testa todas as conexões)
if utils.setup_api():
    st.toast("Todas as APIs conectadas (Texto + Imagem + DB)", icon="✅")
else:
    st.error("⚠️ Erro nas conexões. Verifique o secrets.toml")

# Inicializa variáveis globais de sessão para evitar erros de 'KeyError'
session_keys = [
    'sinopse_en', 'texto_completo_en', 'texto_completo_pt', 
    'tema_atual', 'prompts_visuais', 'critica_atual'
]
for k in session_keys:
    if k not in st.session_state:
        st.session_state[k] = None

st.divider()

if st.session_state.get('texto_completo_pt'):
    st.success(f"📝 Existe um roteiro ativo na memória: **{st.session_state.get('tema_atual', 'Sem título')}**")
