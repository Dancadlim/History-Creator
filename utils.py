import google.generativeai as genai
import edge_tts
import asyncio
import nest_asyncio
from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
import os
import streamlit as st
import requests
import textwrap
import re # Usado para limpar o markdown
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Corrige conflito async do Streamlit
nest_asyncio.apply()

# --- CONFIGURAÇÃO INICIAL (API + FIREBASE) ---
def setup_api():
    # 1. Google Gemini
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    except:
        return False
    
    # 2. Firebase (Inicia apenas uma vez)
    try:
        if not firebase_admin._apps:
            cred_dict = dict(st.secrets["firebase"])
            # Corrige quebra de linha da chave privada
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        return True
    except Exception as e:
        print(f"Erro Firebase: {e}") # Print no terminal para debug
        return False

# --- FUNÇÕES DE TEXTO (AGENTES COM GÊNEROS) ---

def agente_sinopse(tema, nicho, generos):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Act as a creative screenwriter for a {nicho} channel.
    Create an EPIC synopsis for a 30-minute story.
    
    Core Theme: "{tema}"
    Genre/Style Mix: {generos} (You MUST blend these styles).
    
    Output: A single, engaging synopsis in English that hooks the audience immediately.
    """
    return model.generate_content(prompt).text

def agente_titulos(sinopse):
    model = genai.GenerativeModel('gemini-2.5-flash')
    return model.generate_content(f"Based on this synopsis: '{sinopse}', create 8 engaging Chapter Titles in English. Return only the list.").text.split('\n')

def agente_escreve_capitulo(titulo, sinopse, contexto, generos):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Write Chapter: "{titulo}"
    Story Synopsis: "{sinopse}"
    Current Context: {contexto[-500:] if contexto else 'Start of story'}
    
    Style Instructions:
    - Maintain the tone of these genres: {generos}.
    - If "Action", make it fast-paced. If "Romance", focus on emotions.
    - Write approx 400-500 words in English.
    - Narrative documentary style.
    """
    return model.generate_content(prompt).text

def agente_tradutor(texto_en):
    model = genai.GenerativeModel('gemini-2.5-flash')
    return model.generate_content(f"Traduza para Português Brasileiro, mantendo formatação Markdown:\n{texto_en}").text

# --- FIREBASE: SALVAR HISTÓRIA ---
def salvar_historia_db(nicho, tema, generos, texto_pt, texto_en):
    try:
        db = firestore.client()
        
        dados = {
            "nicho": nicho,
            "generos": generos, # Salva separado para filtro
            "tema": tema,
            "roteiro_pt": texto_pt,
            "roteiro_en": texto_en,
            "data_criacao": datetime.now(),
            "status": "Roteirizado"
        }
        
        # Cria documento na coleção 'historias'
        db.collection("historias").add(dados)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar no banco: {e}")
        return False

# --- FUNÇÕES VISUAIS (CAPA) ---
def baixar_fonte():
    font_path = "Roboto-Black.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Black.ttf"
        r = requests.get(url, allow_redirects=True)
        open(font_path, 'wb').write(r.content)
    return font_path

def gerar_capa_simples(titulo, nicho):
    if not os.path.exists("temp"): os.makedirs("temp")
    
    # Fundo Azul Escuro
    img = Image.new('RGB', (1080, 1920), color=(10, 20, 50))
    d = ImageDraw.Draw(img)
    
    try:
        font_file = baixar_fonte()
        font_titulo = ImageFont.truetype(font_file, 90) 
        font_nicho = ImageFont.truetype(font_file, 50)  
    except:
        font_titulo = ImageFont.load_default()
        font_nicho = ImageFont.load_default()
    
    titulo_formatado = "\n".join(textwrap.wrap(titulo, width=15))
    d.text((100, 600), nicho.upper(), fill=(200, 200, 200), font=font_nicho)
    d.text((100, 700), titulo_formatado, fill=(255, 215, 0), font=font_titulo)
    
    path = "temp/capa_gerada.png"
    img.save(path)
    return path

# --- FUNÇÕES DE ÁUDIO (COM TÍTULO FALADO) ---

async def _tts_async(texto, voz, arquivo):
    communicate = edge_tts.Communicate(texto, voz)
    await communicate.save(arquivo)

def gerar_audio(texto_roteiro, idioma, titulo_historia):
    """
    Gera o áudio garantindo que o título seja lido primeiro.
    """
    if not os.path.exists("temp"): os.makedirs("temp")
    
    voz = "pt-BR-AntonioNeural" if idioma == "pt" else "en-US-ChristopherNeural"
    arquivo = f"temp/audio_{idioma}.mp3"
    
    # 1. Monta o texto final para leitura (Título + Pausa + Roteiro)
    # Adicionamos pontuação extra para a IA respirar
    if idioma == 'pt':
        texto_para_ler = f"História: {titulo_historia}.\n\n{texto_roteiro}"
    else:
        texto_para_ler = f"Story: {titulo_historia}.\n\n{texto_roteiro}"

    # 2. Limpeza Profunda do Markdown para Leitura Fluida
    # Remove ##, **, e deixa apenas o texto puro.
    # Ex: "## Capítulo 1" vira "Capítulo 1"
    texto_limpo = texto_para_ler.replace("**", "").replace("*", "")
    texto_limpo = texto_limpo.replace("##", "") 
    
    try:
        asyncio.run(_tts_async(texto_limpo, voz, arquivo))
    except Exception as e:
        st.error(f"Erro TTS: {e}")
        return None
        
    return arquivo

# --- RENDERIZAÇÃO DE VÍDEO ---
def renderizar_video(audio_path, imagem_path, idioma, preview=False):
    if not os.path.exists(audio_path): return None
    
    audio = AudioFileClip(audio_path)
    if preview:
        audio = audio.subclip(0, 60) 
    
    img = ImageClip(imagem_path).set_duration(audio.duration)
    video = CompositeVideoClip([img]).set_audio(audio)
    
    output = f"video_final_{idioma}.mp4"
    video.write_videofile(output, fps=1, codec="libx264", audio_codec="aac", preset="ultrafast")
    return output

# --- FUNÇÃO DE SEGURANÇA (LOGIN) ---
def verificar_senha():
    """
    Trava a execução da página até que a senha correta seja inserida.
    """
    # Se a chave não existir no session_state, cria como False (bloqueado)
    if 'password_correct' not in st.session_state:
        st.session_state.password_correct = False

    # Se já estiver correto, apenas retorna e deixa o código seguir
    if st.session_state.password_correct:
        return

    # --- TELA DE LOGIN ---
    st.markdown("### 🔒 Acesso Restrito")
    st.caption("Este sistema utiliza recursos pagos. Por favor, identifique-se.")
    
    senha_input = st.text_input("Digite a senha de acesso:", type="password")
    
    if st.button("Entrar"):
        # Verifica se a senha bate com o secrets
        try:
            senha_correta = st.secrets["APP_PASSWORD"]
        except:
            st.error("ERRO: A senha não foi configurada no secrets.toml (chave APP_PASSWORD).")
            st.stop()

        if senha_input == senha_correta:
            st.session_state.password_correct = True
            st.rerun() # Recarrega a página para liberar o conteúdo
        else:
            st.error("❌ Senha incorreta.")
    
    # IMPORTANTE: Para a execução de tudo que vem abaixo enquanto não logar
    st.stop()
