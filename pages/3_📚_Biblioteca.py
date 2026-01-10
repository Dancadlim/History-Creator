import streamlit as st
import utils
from firebase_admin import firestore
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Biblioteca", page_icon="📚", layout="wide")

# --- 🔒 TRAVA DE SEGURANÇA (CORRIGIDA) ---
if not utils.verificar_senha():
    st.stop()
# -----------------------------------------

st.title("📚 Biblioteca de Histórias")

# --- CONEXÃO ---
if not utils.setup_api():
    st.error("Erro ao conectar no banco de dados. Verifique o secrets.toml")
    st.stop()

# --- BUSCA DE DADOS ---
@st.cache_data(ttl=60)
def carregar_historias():
    try:
        db = firestore.client()
        docs = db.collection("historias").stream()
        
        lista_historias = []
        for doc in docs:
            dado = doc.to_dict()
            dado['id'] = doc.id
            lista_historias.append(dado)
            
        return lista_historias
    except Exception as e:
        st.error(f"Erro ao baixar histórias: {e}")
        return []

historias = carregar_historias()

if not historias:
    st.info("Nenhuma história encontrada no banco de dados ainda.")
    st.stop()

# --- FILTROS ---
col_search, col_refresh = st.columns([4, 1])
with col_search:
    termo_busca = st.text_input("🔍 Buscar por título, tema ou sinopse:", placeholder="Ex: Davi, Mistério...")
with col_refresh:
    if st.button("🔄 Atualizar"):
        carregar_historias.clear()
        st.rerun()

# --- SEPARAÇÃO ---
lista_biblia = []
lista_geral = []

for item in historias:
    if termo_busca:
        termo = termo_busca.lower()
        tema = item.get('tema', '').lower()
        sinopse = item.get('sinopse', '').lower()
        if termo not in tema and termo not in sinopse:
            continue

    nicho = item.get('nicho', 'Outros')
    if "Bible" in nicho or "Bíblia" in nicho:
        lista_biblia.append(item)
    else:
        lista_geral.append(item)

# --- EXIBIÇÃO ---
tab_biblia, tab_geral = st.tabs([f"✝️ Histórias Bíblicas ({len(lista_biblia)})", f"🌍 Histórias Gerais ({len(lista_geral)})"])

def exibir_lista(lista_items):
    for hist in reversed(lista_items):
        data_show = "Data desconhecida"
        if 'data_criacao' in hist: # Ajustei a chave que usamos no utils (data_criacao)
            try:
                data_show = hist['data_criacao'].strftime("%d/%m/%Y às %H:%M")
            except:
                data_show = str(hist['data_criacao'])

        with st.expander(f"📜 {hist.get('tema', 'Sem Título')} | {data_show}"):
            st.caption(f"**ID:** {hist.get('id')} | **Nicho:** {hist.get('nicho')}")
            st.markdown(f"**Gêneros:** {hist.get('generos', '-')}")
            
            st.markdown("### 📝 Sinopse")
            st.info(hist.get('sinopse', 'Sem sinopse.'))
            
            st.divider()
            sub_tab_pt, sub_tab_en = st.tabs(["🇧🇷 Versão PT-BR", "🇺🇸 Versão Inglês"])
            
            with sub_tab_pt:
                st.text_area("Roteiro Português", hist.get('roteiro_pt', ''), height=300, key=f"pt_{hist['id']}")
            
            with sub_tab_en:
                st.text_area("Roteiro Inglês", hist.get('roteiro_en', ''), height=300, key=f"en_{hist['id']}")
            
            # Botão para carregar no Estúdio (Bônus)
            if st.button("🎬 Carregar no Estúdio", key=f"load_{hist['id']}"):
                st.session_state['texto_completo_pt'] = hist.get('roteiro_pt')
                st.session_state['texto_completo_en'] = hist.get('roteiro_en')
                st.session_state['tema_atual'] = hist.get('tema')
                st.toast("Carregado! Vá para a página Estúdio.")

with tab_biblia:
    if lista_biblia: exibir_lista(lista_biblia)
    else: st.warning("Nenhuma história bíblica encontrada.")

with tab_geral:
    if lista_geral: exibir_lista(lista_geral)
    else: st.warning("Nenhuma história geral encontrada.")
