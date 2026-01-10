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
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Corrige conflito async do Streamlit
nest_asyncio.apply()

# --- CONFIGURAÇÃO INICIAL ---
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
            # Cria credencial a partir do secrets.toml
            cred_dict = dict(st.secrets["firebase"])
            # Corrige a quebra de linha da chave privada se necessário
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        return True
    except Exception as e:
        st.error(f"Erro Firebase: {e}")
        return False

# --- FUNÇÕES DE TEXTO ---
def agente_sinopse(tema, nicho):
    model = genai.GenerativeModel('gemini-2.5-flash')
    return model.generate_content(f"Crie uma sinopse épica em Inglês para uma história de 30min sobre '{tema}' no nicho '{nicho}'. Retorne apenas o texto.").text

def agente_titulos(sinopse):
    model = genai.GenerativeModel('gemini-2.5-flash')
    return model.generate_content(f"Baseado na sinopse '{sinopse}', crie 8 títulos de capítulos em Inglês. Retorne lista.").text.split('\n')

def agente_escreve_capitulo(titulo, sinopse, contexto):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"Escreva o capítulo '{titulo}' (aprox 400 palavras) em Inglês baseado em '{sinopse}'. Contexto anterior: {contexto[-500:] if contexto else ''}"
    return model.generate_content(prompt).text

def agente_tradutor(texto_en):
    model = genai.GenerativeModel('gemini-2.5-flash')
    return model.generate_content(f"Traduza para Português Brasileiro, mantendo formatação Markdown:\n{texto_en}").text

# --- FIREBASE: SALVAR HISTÓRIA ---
def salvar_no_firebase(nicho, tema, sinopse, texto_en, texto_pt):
    try:
        db = firestore.client()
        
        dados = {
            "nicho": nicho,
            "tema": tema,
            "sinopse": sinopse,
            "roteiro_en": texto_en,
            "roteiro_pt": texto_pt,
            "data_criacao": datetime.now(),
            "status": "Roteirizado" # Pode mudar para "Publicado" depois
        }
        
        # Cria um documento na coleção 'historias'
        db.collection("historias").add(dados)
        return True
    except Exception as e:
        print(f"Erro ao salvar: {e}")
        return False

# --- MÍDIA ---
def baixar_fonte():
    font_path = "Roboto-Black.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Black.ttf"
        r = requests.get(url, allow_redirects=True)
        open(font_path, 'wb').write(r.content)
    return font_path

def gerar_capa_simples(titulo, nicho):
    if not os.path.exists("temp"): os.makedirs("temp")
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

async def _tts_async(texto, voz, arquivo):
    communicate = edge_tts.Communicate(texto, voz)
    await communicate.save(arquivo)

def gerar_audio(texto, idioma):
    if not os.path.exists("temp"): os.makedirs("temp")
    voz = "pt-BR-AntonioNeural" if idioma == "pt" else "en-US-ChristopherNeural"
    arquivo = f"temp/audio_{idioma}.mp3"
    texto_limpo = texto.replace("##", "").replace("**", "").replace("*", "")
    try:
        asyncio.run(_tts_async(texto_limpo, voz, arquivo))
    except Exception as e:
        st.error(f"Erro TTS: {e}")
        return None
    return arquivo

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
