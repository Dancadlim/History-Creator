import streamlit as st
import utils
import agentes_escrita
import pandas as pd
import time

st.set_page_config(page_title="Roteiro", page_icon="✍️", layout="wide")

# --- 🔒 TRAVA DE SEGURANÇA ---
if not utils.verificar_senha():
    st.stop()

# --- 🔌 CONEXÃO COM FIREBASE ---
if not utils.setup_api():
    st.error("Erro de Conexão: Verifique se o secrets.toml está configurado corretamente.")
    st.stop()
# -------------------------------

st.title("✍️ Roteirista Multi-Gênero (Modo Arquiteto)")

# --- CONFIGURAÇÃO ---
with st.container(border=True):
    st.subheader("🛠️ Configuração da Narrativa")
    col1, col2 = st.columns(2)
    with col1:
        canal = st.selectbox("Canal / Público", ["Histórias Bíblicas", "Histórias Gerais", "Mistério/Terror", "Curiosidades"])
        generos = st.multiselect(
            "Misturar Gêneros:",
            ["Ação", "Aventura", "Romance", "Comédia", "Drama", "Medieval", "Suspense", "Terror Psicológico", "Investigação"],
            placeholder="Ex: Ação, Medieval..."
        )
    with col2:
        tema = st.text_area("Tema Central:", height=109, placeholder="Ex: Um cavaleiro que se apaixona pela rainha inimiga...")

# --- AÇÃO ---
if st.button("🚀 Iniciar Criação (Arquiteto)", type="primary"):
    if not tema:
        st.warning("Escreva um tema.")
    elif not generos:
        st.warning("Escolha gêneros.")
    else:
        generos_str = ", ".join(generos)
        st.session_state['tema_atual'] = tema 
        
        with st.status(f"Iniciando Motor Criativo...", expanded=True) as status:
            
            # 1. SINOPSE
            st.write("🧠 Criando Sinopse...")
            sinopse = agentes_escrita.agente_sinopse(tema, canal, generos_str)
            st.session_state['sinopse_en'] = sinopse
            st.info(f"Sinopse: {sinopse[:150]}...")
            
            # 2. PLANEJAMENTO (ARQUITETO)
            st.write("📐 Arquiteto desenhando a Escaleta...")
            plano_capitulos = agentes_escrita.agente_planejador(sinopse, generos_str)
            
            # --- CORREÇÃO DO ERRO AQUI ---
            # Mostra o dataframe com o que vier, sem forçar nomes de colunas
            try:
                df_plano = pd.DataFrame(plano_capitulos)
                st.dataframe(df_plano, hide_index=True, use_container_width=True)
            except:
                st.write("⚠️ JSON estruturado irregular, mas seguindo o plano:")
                st.write(plano_capitulos)
            # -----------------------------
            
            # 3. ESCRITA (LOOP GUIADO)
            st.write("✍️ Escrevendo Roteiro...")
            texto_full = ""
            resumo_acumulado = "Story Start."
            prompts_acumulados = []
            
            progresso = st.progress(0)
            total = len(plano_capitulos)
            
            for i, cap_info in enumerate(plano_capitulos):
                # Tenta pegar chaves comuns, se não achar, usa um fallback
                titulo = cap_info.get('title') or cap_info.get('chapter_title') or f"Chapter {i+1}"
                eventos = cap_info.get('events') or cap_info.get('plot_points') or str(cap_info)
                
                status.update(label=f"Escrevendo Cap {i+1}: {titulo}...", state="running")
                
                # Agente V2 escreve baseado no plano
                texto_cap = agentes_escrita.agente_escreve_capitulo_v2(
                    titulo, eventos, sinopse, resumo_acumulado, generos_str
                )
                
                # Agente Visual cria prompts
                prompts_cap = agentes_escrita.agente_visual(texto_cap)
                prompts_acumulados.extend(prompts_cap)
                
                # Resumo para o próximo loop
                novo_resumo = agentes_escrita.agente_resumidor(texto_cap)
                resumo_acumulado += f"\nChapter {i+1}: {novo_resumo}"
                
                texto_full += f"\n\n## {titulo}\n\n{texto_cap}"
                progresso.progress((i+1)/total)
                time.sleep(1) 
            
            st.session_state['texto_completo_en'] = texto_full
            st.session_state['prompts_visuais'] = prompts_acumulados
            
            # 4. TRADUÇÃO
            st.write("🇧🇷 Traduzindo...")
            st.session_state['texto_completo_pt'] = agentes_escrita.agente_tradutor(texto_full)
            
            status.update(label="Concluído!", state="complete", expanded=False)
            st.success("História pronta!")

# --- VISUALIZAÇÃO E SAVE ---
if st.session_state.get('texto_completo_pt'):
    st.divider()
    if st.button("💾 Salvar no Firebase", type="primary"):
        generos_salvar = ", ".join(generos) if generos else "Geral"
        
        if utils.setup_api():
            sucesso = utils.salvar_historia_db(
                f"{canal} ({generos_salvar})", 
                tema, 
                generos_salvar,
                st.session_state['texto_completo_pt'], 
                st.session_state['texto_completo_en'],
                st.session_state.get('prompts_visuais', [])
            )
            if sucesso: st.toast("Salvo!", icon="✅")
        else:
             st.error("Erro crítico de conexão ao tentar salvar.")

    tab_pt, tab_en, tab_prompts = st.tabs(["🇧🇷 PT", "🇺🇸 EN", "🎨 Prompts"])
    with tab_pt: st.text_area("PT", st.session_state['texto_completo_pt'], height=500)
    with tab_en: st.text_area("EN", st.session_state['texto_completo_en'], height=500)
    with tab_prompts: st.write(st.session_state.get('prompts_visuais', []))
