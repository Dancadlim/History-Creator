import streamlit as st
import utils
from firebase_admin import firestore
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Biblioteca", page_icon="📚", layout="wide")
st.title("📚 Biblioteca de Histórias")

# --- CONEXÃO ---
# Garante que a API/Firebase está conectada
if not utils.setup_api():
    st.error("Erro ao conectar no banco de dados. Verifique o secrets.toml")
    st.stop()

# --- BUSCA DE DADOS ---
@st.cache_data(ttl=60) # Cache de 60 segundos para não gastar leitura do banco a toda hora
def carregar_historias():
    try:
        db = firestore.client()
        # Pega todas as histórias ordenadas por data (se possível)
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

# Carrega dados
historias = carregar_historias()

if not historias:
    st.info("Nenhuma história encontrada no banco de dados ainda.")
    st.stop()

# --- FILTROS E BUSCA ---
col_search, col_refresh = st.columns([4, 1])
with col_search:
    termo_busca = st.text_input("🔍 Buscar por título, tema ou sinopse:", placeholder="Ex: Davi, Mistério...")
with col_refresh:
    if st.button("🔄 Atualizar"):
        carregar_historias.clear()
        st.rerun()

# --- SEPARAÇÃO POR CATEGORIA ---
lista_biblia = []
lista_geral = []

for item in historias:
    # Filtro de Busca (Se tiver termo, verifica se bate com tema ou sinopse)
    if termo_busca:
        termo = termo_busca.lower()
        tema = item.get('tema', '').lower()
        sinopse = item.get('sinopse', '').lower()
        if termo not in tema and termo not in sinopse:
            continue # Pula este item se não bater com a busca

    # Separação por Abas
    nicho = item.get('nicho', 'Outros')
    if "Bible" in nicho or "Bíblia" in nicho:
        lista_biblia.append(item)
    else:
        lista_geral.append(item)

# --- EXIBIÇÃO ---
tab_biblia, tab_geral = st.tabs([f"✝️ Histórias Bíblicas ({len(lista_biblia)})", f"🌍 Histórias Gerais ({len(lista_geral)})"])

def exibir_lista(lista_items):
    # Inverte a lista para mostrar os mais recentes primeiro
    for hist in reversed(lista_items):
        # Tenta formatar a data
        data_show = "Data desconhecida"
        if 'data' in hist:
            try:
                # Se for objeto datetime do Firestore
                data_show = hist['data'].strftime("%d/%m/%Y às %H:%M")
            except:
                data_show = str(hist['data'])

        # O Expander é o "Clicar para abrir projeto"
        with st.expander(f"📜 {hist.get('tema', 'Sem Título')} | {data_show}"):
            st.caption(f"**ID:** {hist.get('id')} | **Nicho:** {hist.get('nicho')}")
            
            # Sinopse
            st.markdown("### 📝 Sinopse")
            st.info(hist.get('sinopse', 'Sem sinopse.'))
            
            # Conteúdo Full
            st.divider()
            sub_tab_pt, sub_tab_en = st.tabs(["🇧🇷 Versão PT-BR", "🇺🇸 Versão Inglês"])
            
            with sub_tab_pt:
                st.text_area("Roteiro Português", hist.get('roteiro_pt', ''), height=300, key=f"pt_{hist['id']}")
                if st.button("Copiar PT", key=f"btn_pt_{hist['id']}"):
                    st.toast("Texto copiado (mentira, o streamlit ainda não deixa copiar nativo, mas tá selecionável!)")
            
            with sub_tab_en:
                st.text_area("Roteiro Inglês", hist.get('roteiro_en', ''), height=300, key=f"en_{hist['id']}")

# Renderiza as abas
with tab_biblia:
    if lista_biblia:
        exibir_lista(lista_biblia)
    else:
        st.warning("Nenhuma história bíblica encontrada.")

with tab_geral:
    if lista_geral:
        exibir_lista(lista_geral)
    else:
        st.warning("Nenhuma história geral encontrada.")
