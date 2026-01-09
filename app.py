import streamlit as st
import google.generativeai as genai
import time

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Fábrica de Histórias Longas", page_icon="📚", layout="wide")
st.title("📚 Gerador de Histórias Longas (20-40 min)")

# --- API ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("Configure o secrets.toml com a GOOGLE_API_KEY")
    st.stop()

# --- ESTADO DA SESSÃO (Memória do Streamlit) ---
if 'capitulos_gerados' not in st.session_state:
    st.session_state['capitulos_gerados'] = [] # Guarda o texto de cada capítulo
if 'roteiro_completo' not in st.session_state:
    st.session_state['roteiro_completo'] = ""
if 'titulos_capitulos' not in st.session_state:
    st.session_state['titulos_capitulos'] = []

# --- FUNÇÕES ---
def gerar_outline(tema, nicho):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Atue como um autor de best-sellers. Crie um esboço (outline) para uma história profunda sobre "{tema}" no nicho "{nicho}".
    O objetivo é ter uma narração de aproximadamente 30 minutos.
    Crie APENAS uma lista com 8 títulos de capítulos que criem um arco narrativo completo.
    Retorne apenas os títulos, um por linha.
    """
    resp = model.generate_content(prompt)
    return resp.text.split('\n')

def escrever_capitulo(titulo, contexto_anterior, nicho):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Escreva o capítulo: "{titulo}" para uma história do nicho {nicho}.
    
    Contexto anterior: {contexto_anterior[-500:] if contexto_anterior else "Início da história."}
    
    Regras:
    1. Escreva aproximadamente 500 a 600 palavras.
    2. Linguagem imersiva, detalhada e emocionante (estilo audiobook/documentário).
    3. Foque na narrativa e descrição de cenários/sentimentos.
    4. NÃO coloque metadados, apenas o texto da narração.
    """
    resp = model.generate_content(prompt)
    return resp.text

# --- INTERFACE ---
with st.sidebar:
    nicho = st.selectbox("Nicho", ["Bíblico", "Mistério/Crime", "História Real"])
    tema = st.text_area("Tema da História", height=100)
    if st.button("1. Planejar Capítulos"):
        titulos = gerar_outline(tema, nicho)
        # Limpa sujeira da lista se houver linhas vazias
        st.session_state['titulos_capitulos'] = [t for t in titulos if t.strip() != ""]
        st.session_state['capitulos_gerados'] = []
        st.session_state['roteiro_completo'] = ""
        st.success("Estrutura criada! Veja ao lado.")

# --- ÁREA PRINCIPAL ---
if st.session_state['titulos_capitulos']:
    st.subheader("📖 Estrutura da História")
    
    # Mostra os capítulos planejados
    for i, tit in enumerate(st.session_state['titulos_capitulos']):
        st.text(f"Capítulo {i+1}: {tit}")
    
    st.divider()
    
    if st.button("2. Escrever História Completa (Isso vai demorar um pouco)"):
        texto_acumulado = ""
        progresso = st.progress(0)
        total = len(st.session_state['titulos_capitulos'])
        
        placeholder = st.empty()
        
        for index, titulo in enumerate(st.session_state['titulos_capitulos']):
            with placeholder.container():
                st.info(f"Escrevendo Capítulo {index+1}/{total}: {titulo}...")
            
            # Gera o texto do capítulo
            texto_cap = escrever_capitulo(titulo, texto_acumulado, nicho)
            
            # Adiciona ao montante
            st.session_state['capitulos_gerados'].append(f"\n\n## {titulo}\n\n{texto_cap}")
            texto_acumulado += texto_cap
            
            # Atualiza barra de progresso
            progresso.progress((index + 1) / total)
            
            # Pequena pausa para não estourar limite da API (se houver)
            time.sleep(1)
        
        st.session_state['roteiro_completo'] = texto_acumulado
        placeholder.success("História Completa Gerada!")

# --- RESULTADO FINAL ---
if st.session_state['roteiro_completo']:
    st.subheader("📜 Roteiro Final")
    
    total_palavras = len(st.session_state['roteiro_completo'].split())
    tempo_estimado = total_palavras / 140
    
    st.metric("Total de Palavras", total_palavras)
    st.metric("Tempo Estimado de Narração", f"{tempo_estimado:.1f} minutos")
    
    st.text_area("Copie seu texto:", st.session_state['roteiro_completo'], height=400)
    
    st.info("Próximo passo: Gerar Áudio (Edge-TTS) para esse textão.")
