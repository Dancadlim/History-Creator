import streamlit as st
import google.generativeai as genai
import time

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Fábrica de Épicos IA", page_icon="🏛️", layout="wide")
st.title("🏛️ Gerador de Histórias Longas (EN -> PT)")

# --- API ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("Configure o secrets.toml com a GOOGLE_API_KEY")
    st.stop()

# --- MEMÓRIA DA SESSÃO ---
# Armazena cada etapa para não perder nada
keys = ['sinopse_en', 'critica_sinopse', 'titulos_en', 'texto_completo_en', 'texto_completo_pt']
for k in keys:
    if k not in st.session_state:
        st.session_state[k] = None

# --- FUNÇÕES DE AGENTES ---

def agente_roteirista_sinopse(tema, nicho):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Role: Professional Screenwriter for {nicho}.
    Task: Create a deep, engaging premise (synopsis) for a 30-minute story about: "{tema}".
    Format: A single paragraph summarising the narrative arc, the emotional conflict, and the resolution.
    Language: English.
    """
    return model.generate_content(prompt).text

def agente_critico(sinopse):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Role: Harsh Literary Critic.
    Task: Analyze this synopsis: "{sinopse}".
    Output: Give a score from 0 to 10. If below 8, explain why briefly. If 8+, just say "APPROVED".
    """
    return model.generate_content(prompt).text

def agente_estruturador(sinopse):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Based on this synopsis: "{sinopse}".
    Create a list of 8 Chapter Titles that build suspense and engagement.
    Return ONLY the titles, one per line.
    """
    resp = model.generate_content(prompt)
    return resp.text.split('\n')

def agente_escritor_capitulo(titulo, sinopse, contexto_anterior):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Write Chapter: "{titulo}".
    Story Premise: "{sinopse}".
    Previous Context: {contexto_anterior[-600:] if contexto_anterior else "Start of story"}.
    
    Guidelines:
    1. Write approx 500 words.
    2. Style: Immersive storytelling, biblical/historical documentary style.
    3. Focus on sensory details and emotion.
    4. Language: English.
    """
    return model.generate_content(prompt).text

def agente_tradutor(texto_en):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Translate the following text to Portuguese (Brazil).
    Maintain the epic, emotional, and narrative tone.
    Adapt expressions to sound natural in Portuguese, do not translate literally.
    
    Text:
    {texto_en}
    """
    return model.generate_content(prompt).text

# --- INTERFACE ---

with st.sidebar:
    st.header("1. Definição")
    nicho = st.selectbox("Nicho", ["Bible Stories", "Mystery/Horror", "True History"])
    tema = st.text_area("Tema (pode escrever em PT)", height=100)
    
    if st.button("Gerar Sinopse"):
        st.session_state['sinopse_en'] = agente_roteirista_sinopse(tema, nicho)
        # Ao gerar nova sinopse, reseta o resto
        st.session_state['critica_sinopse'] = None
        st.session_state['titulos_en'] = None

# --- FLUXO PRINCIPAL ---

# 1. SINOPSE E CRÍTICA
if st.session_state['sinopse_en']:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📝 Sinopse (English)")
        st.info(st.session_state['sinopse_en'])
    with col2:
        if st.button("Chamar Agente Crítico"):
            st.session_state['critica_sinopse'] = agente_critico(st.session_state['sinopse_en'])
        
        if st.session_state['critica_sinopse']:
            st.warning(f"Parecer do Crítico: {st.session_state['critica_sinopse']}")

    st.divider()

    # 2. APROVAÇÃO E ESTRUTURA
    if st.button("Aprovar e Gerar Capítulos"):
        st.session_state['titulos_en'] = agente_estruturador(st.session_state['sinopse_en'])

# 3. ESCRITA DOS CAPÍTULOS
if st.session_state['titulos_en']:
    st.subheader("📖 Estrutura dos Capítulos")
    st.write(st.session_state['titulos_en'])
    
    if st.button("Escrever História Completa (EN)"):
        texto_full = ""
        progresso = st.progress(0)
        total = len(st.session_state['titulos_en'])
        placeholder = st.empty()
        
        for i, titulo in enumerate(st.session_state['titulos_en']):
            if titulo.strip():
                with placeholder.container():
                    st.write(f"✍️ Writing Chapter {i+1}: {titulo}...")
                
                cap_texto = agente_escritor_capitulo(titulo, st.session_state['sinopse_en'], texto_full)
                texto_full += f"\n\n## {titulo}\n\n{cap_texto}"
                progresso.progress((i+1)/total)
                time.sleep(1) # Respeito à API
        
        st.session_state['texto_completo_en'] = texto_full
        placeholder.success("História em Inglês Concluída!")

# 4. EXIBIÇÃO E TRADUÇÃO
if st.session_state['texto_completo_en']:
    tab_en, tab_pt = st.tabs(["🇺🇸 English (Original)", "🇧🇷 Português (Traduzido)"])
    
    with tab_en:
        st.text_area("Full Script (EN)", st.session_state['texto_completo_en'], height=400)
    
    with tab_pt:
        if st.session_state['texto_completo_pt'] is None:
            if st.button("Traduzir para Português"):
                with st.spinner("Traduzindo com contexto narrativo..."):
                    # Traduzimos em blocos grandes para manter coerência
                    # (Num app real, traduziríamos capítulo por capítulo, aqui faremos direto pro MVP)
                    st.session_state['texto_completo_pt'] = agente_tradutor(st.session_state['texto_completo_en'])
                    st.rerun()
        else:
            st.text_area("Roteiro Completo (PT)", st.session_state['texto_completo_pt'], height=400)
            st.success("Temos os dois textos prontos! Próximo passo: Narração.")
