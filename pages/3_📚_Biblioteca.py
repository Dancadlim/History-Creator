import streamlit as st
import utils
from firebase_admin import firestore
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Biblioteca", page_icon="📚", layout="wide")

# --- 🔒 TRAVA DE SEGURANÇA ---
if not utils.verificar_senha():
    st.stop()

st.title("📚 Biblioteca de Histórias")

# --- CONEXÃO ---
# O utils.setup_api() agora garante que o Firebase (e o Google) estão prontos
if not utils.setup_api():
    st.error("Erro ao conectar nos serviços. Verifique o secrets.toml")
    st.stop()

# --- BUSCA DE DADOS ---
@st.cache_data(ttl=5) # Cache curto para atualização rápida
def carregar_historias():
    try:
        db = firestore.client()
        # Tenta ordenar por data (requer índice no Firebase na primeira vez)
        try:
            docs = db.collection("historias").order_by("data_criacao", direction=firestore.Query.DESCENDING).stream()
        except:
            # Fallback se não tiver índice ainda
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
    st.info("Nenhuma história encontrada no banco de dados.")
    st.stop()

# --- FILTROS ---
with st.container(border=True):
    col_search, col_status, col_refresh = st.columns([3, 2, 1])
    
    with col_search:
        termo_busca = st.text_input("🔍 Buscar:", placeholder="Título, tema ou sinopse...")
        
    with col_status:
        filtro_status = st.selectbox(
            "Filtrar por Etapa:",
            ["Todos", "Roteiro Pronto", "Aguardando Postagem", "Postado"]
        )
        
    with col_refresh:
        st.write("") 
        if st.button("🔄 Atualizar"):
            carregar_historias.clear()
            st.rerun()

# --- SEPARAÇÃO ---
lista_biblia = []
lista_geral = []

for item in historias:
    # 1. Filtro de Texto
    if termo_busca:
        termo = termo_busca.lower()
        tema = item.get('tema', '').lower()
        sinopse = item.get('sinopse', '').lower()
        if termo not in tema and termo not in sinopse:
            continue

    # 2. Filtro de Status
    status_item = item.get('status', 'Roteiro Pronto')
    if filtro_status != "Todos" and status_item != filtro_status:
        continue

    # 3. Separação por Nicho
    nicho = item.get('nicho', 'Outros')
    if "Bible" in nicho or "Bíblia" in nicho or "Biblicas" in nicho:
        lista_biblia.append(item)
    else:
        lista_geral.append(item)

# --- FUNÇÃO DE EXIBIÇÃO ---
def exibir_lista(lista_items):
    for hist in lista_items:
        # Ícone visual
        status_atual = hist.get('status', 'Roteiro Pronto')
        icone_status = "🔴"
        if status_atual == "Aguardando Postagem": icone_status = "🟠"
        if status_atual == "Postado": icone_status = "🟢"
        
        tema_display = hist.get('tema', 'Sem Título')
        
        with st.expander(f"{icone_status} {tema_display}"):
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.caption(f"**ID:** {hist.get('id')}")
            c2.caption(f"**Nicho:** {hist.get('nicho')}")
            c3.caption(f"**Status:** {status_atual}")
            
            st.markdown(f"**Gêneros:** {hist.get('generos', '-')}")
            
            # --- BOTÃO MÁGICO DE CARREGAR ---
            st.info("💡 **Produção:**")
            if st.button(f"🎬 Carregar no Estúdio", key=f"load_{hist['id']}", type="primary"):
                # 1. Carrega os Dados Principais
                st.session_state['texto_completo_pt'] = hist.get('roteiro_pt')
                st.session_state['texto_completo_en'] = hist.get('roteiro_en')
                st.session_state['tema_atual'] = hist.get('tema')
                st.session_state['prompts_visuais'] = hist.get('prompts', [])
                
                # 2. LIMPEZA DE SESSÃO (IMPORTANTE PARA O NOVO FLUXO)
                # Reseta caminhos de arquivos antigos
                st.session_state['caminhos_imagens'] = []
                st.session_state['caminhos_audio'] = {"pt": None, "en": None}
                
                # Reseta Críticas antigas (para não misturar feedbacks)
                if 'critica_atual' in st.session_state:
                    del st.session_state['critica_atual']
                
                st.toast("Roteiro carregado! Vá para a aba 'Estúdio'.", icon="🚀")

            st.divider()

            # Visualização Rápida
            t_sinopse, t_pt, t_en, t_prompts = st.tabs(["📝 Sinopse", "🇧🇷 PT", "🇺🇸 EN", "🎨 Prompts"])
            
            with t_sinopse: st.write(hist.get('sinopse', '...'))
            with t_pt: st.text_area("PT", hist.get('roteiro_pt', ''), height=150, key=f"pt_{hist['id']}")
            with t_en: st.text_area("EN", hist.get('roteiro_en', ''), height=150, key=f"en_{hist['id']}")
            with t_prompts: 
                prompts = hist.get('prompts', [])
                if prompts:
                    for i, p in enumerate(prompts):
                        st.text(f"{i+1}. {p}")
                else:
                    st.warning("Sem prompts salvos.")

            st.divider()
            
            # Gestão de Status
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if status_atual == "Roteiro Pronto":
                    if st.button("⬇️ Marcar Baixado", key=f"bx_{hist['id']}"):
                        utils.atualizar_status_historia(hist['id'], "Aguardando Postagem")
                        st.rerun()
            with col_b2:
                if status_atual != "Postado":
                    if st.button("✅ Marcar Postado", key=f"pst_{hist['id']}"):
                        utils.atualizar_status_historia(hist['id'], "Postado")
                        st.rerun()

# --- RENDERIZAÇÃO DAS ABAS ---
tab_biblia, tab_geral = st.tabs([f"✝️ Bíblicas ({len(lista_biblia)})", f"🌍 Gerais ({len(lista_geral)})"])

with tab_biblia:
    if lista_biblia: exibir_lista(lista_biblia)
    else: st.warning("Nenhuma história bíblica encontrada.")

with tab_geral:
    if lista_geral: exibir_lista(lista_geral)
    else: st.warning("Nenhuma história geral encontrada.")
