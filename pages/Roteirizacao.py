import streamlit as st
import utils
import time

st.set_page_config(page_title="Roteiro", page_icon="✍️", layout="wide")

# --- 🔒 TRAVA DE SEGURANÇA ---
utils.verificar_senha()

st.title("✍️ Roteirista Multi-Gênero")


# --- CONFIGURAÇÃO DA HISTÓRIA ---
with st.container(border=True):
    st.subheader("🛠️ Configuração da Narrativa")
    
    col1, col2 = st.columns(2)
    with col1:
        # Canal Alvo (Para saber onde vai postar)
        canal = st.selectbox(
            "Canal / Público Alvo", 
            ["Histórias Bíblicas", "Histórias Gerais", "Mistério/Terror", "Curiosidades"]
        )
        
        # MULTI-SELEÇÃO DE GÊNEROS (NOVIDADE)
        generos = st.multiselect(
            "Misturar Gêneros (Escolha 1 ou mais):",
            [
                "Ação", "Aventura", "Romance", "Comédia", "Drama", 
                "Medieval", "Suspense", "Escolar", "Sci-Fi", 
                "Fantasia", "Terror Psicológico", "Cyberpunk", "Investigação"
            ],
            help="A IA vai combinar todos os estilos escolhidos.",
            placeholder="Ex: Ação, Medieval..."
        )
        
    with col2:
        tema = st.text_area("Tema Central / Ideia:", height=109, placeholder="Ex: Um cavaleiro que se apaixona pela rainha inimiga...")

# --- AÇÃO ---
if st.button("🚀 Iniciar Criação", type="primary"):
    if not tema:
        st.warning("Por favor, escreva um tema.")
    elif not generos:
        st.warning("Escolha pelo menos um gênero (ex: Drama).")
    else:
        # Transforma a lista de gêneros em texto (ex: "Ação, Romance")
        generos_str = ", ".join(generos)
        
        with st.status(f"Escrevendo história de {generos_str}...", expanded=True) as status:
            
            st.write("🧠 Criando Sinopse Criativa...")
            # Passamos os gêneros para o agente
            sinopse = utils.agente_sinopse(tema, canal, generos_str)
            st.session_state['sinopse_en'] = sinopse
            
            st.write("📐 Estruturando Capítulos...")
            titulos = utils.agente_titulos(sinopse)
            
            st.write("✍️ Escrevendo Roteiro Completo...")
            texto_full = ""
            progresso = st.progress(0)
            
            for i, t in enumerate(titulos):
                if t.strip():
                    # Passamos os gêneros também para o escritor manter o tom
                    cap = utils.agente_escreve_capitulo(t, sinopse, texto_full, generos_str)
                    texto_full += f"\n\n## {t}\n\n{cap}"
                    progresso.progress((i+1)/len(titulos))
                    time.sleep(1)
            
            st.session_state['texto_completo_en'] = texto_full
            
            st.write("🇧🇷 Traduzindo e Adaptando...")
            st.session_state['texto_completo_pt'] = utils.agente_tradutor(texto_full)
            
            status.update(label="Roteiro Finalizado!", state="complete", expanded=False)
            st.success("História pronta!")

# --- VISUALIZAÇÃO ---
if st.session_state.get('texto_completo_pt'):
    st.divider()
    col_save, col_info = st.columns([1, 4])
    
    with col_save:
        # Salva também os gêneros no banco para você filtrar depois
        if st.button("💾 Salvar no Firebase", type="primary"):
            generos_salvar = ", ".join(generos) if generos else "Geral"
            sucesso = utils.salvar_historia_db(
                f"{canal} ({generos_salvar})", # Salva nicho + gêneros juntos
                tema, 
                st.session_state['texto_completo_pt'], 
                st.session_state['texto_completo_en']
            )
            if sucesso:
                st.toast("Salvo com sucesso!", icon="✅")

    tab_pt, tab_en = st.tabs(["🇧🇷 Português", "🇺🇸 English"])
    with tab_pt:
        st.text_area("Roteiro PT", st.session_state['texto_completo_pt'], height=500)
    with tab_en:
        st.text_area("Roteiro EN", st.session_state['texto_completo_en'], height=500)
