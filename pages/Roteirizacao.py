import streamlit as st
import utils
import agentes_escrita
import pandas as pd
import time

st.set_page_config(page_title="Roteiro", page_icon="✍️", layout="wide")

if not utils.verificar_senha(): st.stop()
if not utils.setup_api():
    st.error("Erro Conexão Firebase.")
    st.stop()

st.title("✍️ Roteirista Autônomo (Feedback Loop)")

# --- CONFIG ---
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        canal = st.selectbox("Nicho", ["Mistério/Terror", "Histórias Bíblicas", "Curiosidades"])
        generos = st.multiselect("Gêneros", ["Suspense", "Terror Psicológico", "Investigação"], default=["Suspense"])
    with col2:
        tema = st.text_area("Tema:", height=100, placeholder="Ex: Amigos presos numa cabana...")

# --- 1. GERAÇÃO INICIAL ---
if st.button("🚀 1. Criar Rascunho (Arquiteto)", type="primary"):
    if tema and generos:
        generos_str = ", ".join(generos)
        st.session_state['tema_atual'] = tema
        st.session_state['generos_str'] = generos_str
        
        with st.status("Escrevendo V1...", expanded=True) as status:
            # Sinopse
            sinopse = agentes_escrita.agente_sinopse(tema, canal, generos_str)
            st.session_state['sinopse_en'] = sinopse
            
            # Planejamento
            plano = agentes_escrita.agente_planejador(sinopse, generos_str)
            try:
                st.dataframe(pd.DataFrame(plano)[['title', 'events']], hide_index=True)
            except:
                st.write(plano)
            
            # Escrita
            texto_full = ""
            resumo = "Start."
            prompts = []
            progresso = st.progress(0)
            
            for i, cap in enumerate(plano):
                tit = cap.get('title', f"Ch {i}")
                evt = cap.get('events', '')
                status.update(label=f"Escrevendo {tit}...")
                
                txt = agentes_escrita.agente_escreve_capitulo_v2(tit, evt, sinopse, resumo, generos_str)
                prompts.extend(agentes_escrita.agente_visual(txt))
                resumo += f"\n{agentes_escrita.agente_resumidor(txt)}"
                texto_full += f"\n\n## {tit}\n\n{txt}"
                progresso.progress((i+1)/len(plano))
            
            st.session_state['texto_completo_en'] = texto_full
            st.session_state['prompts_visuais'] = prompts
            
            st.write("Traduzindo...")
            st.session_state['texto_completo_pt'] = agentes_escrita.agente_tradutor(texto_full)
            status.update(label="Rascunho Pronto!", state="complete")
            st.rerun()

# --- 2. CICLO DE REFINAMENTO ---
if st.session_state.get('texto_completo_pt'):
    st.divider()
    st.subheader("🔁 Ciclo de Refinamento")
    
    col_crit, col_rewrite = st.columns(2)
    
    with col_crit:
        if st.button("🕵️ 2. Chamar o Crítico"):
            with st.spinner("Analisando..."):
                critica = agentes_escrita.agente_critico(
                    st.session_state['texto_completo_pt'], 
                    st.session_state.get('generos_str', 'Terror')
                )
                st.session_state['critica_atual'] = critica
                st.rerun()

    with col_rewrite:
        tem_critica = 'critica_atual' in st.session_state
        if st.button("✍️ 3. Aplicar Correções (Reescrever)", disabled=not tem_critica, type="primary"):
            with st.spinner("Reescrevendo a história..."):
                novo_texto = agentes_escrita.agente_reescritor(
                    st.session_state['texto_completo_pt'],
                    st.session_state['critica_atual'],
                    st.session_state.get('generos_str', 'Terror')
                )
                st.session_state['texto_completo_pt'] = novo_texto
                del st.session_state['critica_atual'] # Limpa para nova crítica
                st.toast("História Reescrita!", icon="✨")
                st.rerun()

    if st.session_state.get('critica_atual'):
        st.warning("⚠️ Notas do Crítico:")
        st.markdown(st.session_state['critica_atual'])

    # Editor Manual
    t_pt, t_en = st.tabs(["🇧🇷 Roteiro PT (Editável)", "🇺🇸 Original EN"])
    with t_pt:
        novo_pt = st.text_area("Texto Final", st.session_state['texto_completo_pt'], height=500)
        st.session_state['texto_completo_pt'] = novo_pt
    with t_en:
        st.text_area("EN", st.session_state.get('texto_completo_en', ''), height=500)

    # --- 3. SALVAR ---
    st.divider()
    if st.button("💾 4. Aprovar e Salvar", type="secondary", use_container_width=True):
        if utils.setup_api():
            utils.salvar_historia_db(
                f"{canal}", st.session_state.get('tema_atual'), st.session_state.get('generos_str'),
                st.session_state['texto_completo_pt'],
                st.session_state.get('texto_completo_en', ''),
                st.session_state.get('prompts_visuais', [])
            )
            st.success("Salvo! Vá para o Estúdio.")
