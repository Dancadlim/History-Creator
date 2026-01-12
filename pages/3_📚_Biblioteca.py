import streamlit as st
import utils
from firebase_admin import firestore
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Biblioteca", page_icon="📚", layout="wide")

# --- 🔒 TRAVA DE SEGURANÇA ---
if not utils.verificar_senha():
    st.stop()
# -----------------------------

st.title("📚 Biblioteca de Histórias")

# --- CONEXÃO ---
if not utils.setup_api():
    st.error("Erro ao conectar no banco de dados. Verifique o secrets.toml")
    st.stop()

# --- BUSCA DE DADOS ---
# Reduzi o cache para 5s para você ver as mudanças de status rápido durante os testes
@st.cache_data(ttl=5) 
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

# --- FILTROS E BUSCA ---
with st.container(border=True):
    col_search, col_status, col_refresh = st.columns([3, 2, 1])
    
    with col_search:
        termo_busca = st.text_input("🔍 Buscar:", placeholder="Título, tema ou sinopse...")
        
    with col_status:
        # Novo filtro de workflow
        filtro_status = st.selectbox(
            "Filtrar por Etapa:",
            ["Todos", "Roteiro Pronto", "Aguardando Postagem", "Postado"]
        )
        
    with col_refresh:
        st.write("") # Espaçamento
        if st.button("🔄 Atualizar Lista"):
            carregar_historias.clear()
            st.rerun()

# --- SEPARAÇÃO E FILTRAGEM ---
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
    status_item = item.get('status', 'Roteiro Pronto') # Padrão se não tiver campo
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
    # Inverte para os mais novos aparecerem primeiro
    for hist in reversed(lista_items):
        
        # Formatação de Data
        data_show = "Data desc."
        if 'data_criacao' in hist:
            try:
                data_show = hist['data_criacao'].strftime("%d/%m/%Y %H:%M")
            except:
                data_show = str(hist['data_criacao'])

        # Ícone visual do status
        status_atual = hist.get('status', 'Roteiro Pronto')
        icone_status = "🔴" # Roteiro Pronto
        if status_atual == "Aguardando Postagem": icone_status = "🟠"
        if status_atual == "Postado": icone_status = "🟢"

        # Título do Cartão
        titulo_card = f"{icone_status} {hist.get('tema', 'Sem Título')} | {data_show}"

        with st.expander(titulo_card):
            # Cabeçalho do Card
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.caption(f"**ID:** {hist.get('id')}")
            c2.caption(f"**Nicho:** {hist.get('nicho')}")
            c3.caption(f"**Status:** {status_atual}")
            
            st.markdown(f"**Gêneros:** {hist.get('generos', '-')}")
            
            # Botão Principal de Produção
            st.info("💡 **Ação Recomendada:**")
            if st.button(f"🎬 Carregar no Estúdio para Produzir", key=f"load_{hist['id']}", type="primary"):
                # Carrega tudo na sessão para o arquivo Estudio.py usar
                st.session_state['texto_completo_pt'] = hist.get('roteiro_pt')
                st.session_state['texto_completo_en'] = hist.get('roteiro_en')
                st.session_state['tema_atual'] = hist.get('tema')
                st.session_state['prompts_visuais'] = hist.get('prompts') # Carrega os prompts salvos
                
                st.toast("Roteiro carregado! Vá para a aba 'Estúdio'.", icon="🚀")

            st.divider()

            # Abas de Conteúdo
            t_sinopse, t_pt, t_en, t_prompts = st.tabs(["📝 Sinopse", "🇧🇷 Roteiro PT", "🇺🇸 Roteiro EN", "🎨 Prompts"])
            
            with t_sinopse:
                st.write(hist.get('sinopse', 'Sem sinopse.'))
            
            with t_pt:
                st.text_area("PT", hist.get('roteiro_pt', ''), height=200, key=f"pt_{hist['id']}")
            
            with t_en:
                st.text_area("EN", hist.get('roteiro_en', ''), height=200, key=f"en_{hist['id']}")
                
            with t_prompts:
                # Mostra os prompts se tiver
                prompts = hist.get('prompts', [])
                if prompts:
                    for i, p in enumerate(prompts):
                        st.text(f"{i+1}. {p}")
                else:
                    st.warning("Nenhum prompt visual salvo para esta história.")

            st.divider()
            
            # --- ÁREA DE GESTÃO DE STATUS ---
            st.markdown("#### ⚙️ Gestão de Fluxo")
            col_b1, col_b2 = st.columns(2)
            
            with col_b1:
                # Botão para marcar que já baixou os vídeos
                if status_atual == "Roteiro Pronto":
                    if st.button("⬇️ Marcar como Baixado (Vídeos Prontos)", key=f"bx_{hist['id']}"):
                        if utils.atualizar_status_historia(hist['id'], "Aguardando Postagem"):
                            st.toast("Status atualizado!", icon="✅")
                            carregar_historias.clear()
                            st.rerun()
                else:
                    st.caption("Videos já baixados.")

            with col_b2:
                # Botão para marcar que já postou
                if status_atual != "Postado":
                    if st.button("✅ Marcar como Postado", key=f"pst_{hist['id']}"):
                        if utils.atualizar_status_historia(hist['id'], "Postado"):
                            st.toast("Parabéns! História finalizada.", icon="🎉")
                            carregar_historias.clear()
                            st.rerun()
                else:
                    st.success("História finalizada e postada!")

# --- RENDERIZAÇÃO DAS ABAS PRINCIPAIS ---
tab_biblia, tab_geral = st.tabs([f"✝️ Histórias Bíblicas ({len(lista_biblia)})", f"🌍 Histórias Gerais ({len(lista_geral)})"])

with tab_biblia:
    if lista_biblia:
        exibir_lista(lista_biblia)
    else:
        st.warning("Nenhuma história encontrada neste filtro.")

with tab_geral:
    if lista_geral:
        exibir_lista(lista_geral)
    else:
        st.warning("Nenhuma história encontrada neste filtro.")
