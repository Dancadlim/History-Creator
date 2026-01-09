# Arquivo: utils.py
# ESSE ARQUIVO NÃO APARECE NO SITE, ELE É O BASTIDOR
import google.generativeai as genai
import edge_tts
import asyncio
import nest_asyncio
from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
import os
import streamlit as st

# Corrige conflito async do Streamlit
nest_asyncio.apply()

# Configura API (Pega do secrets)
def setup_api():
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        return True
    except:
        return False

# --- FUNÇÕES DE TEXTO (GEMINI) ---
def agente_sinopse(tema, nicho):
    model = genai.GenerativeModel('gemini-2.5-flash')
    return model.generate_content(f"Crie uma sinopse épica em Inglês para uma história de 30min sobre '{tema}' no nicho '{nicho}'.").text

def agente_titulos(sinopse):
    model = genai.GenerativeModel('gemini-2.5-flash')
    return model.generate_content(f"Baseado na sinopse '{sinopse}', crie 8 títulos de capítulos em Inglês. Retorne apenas a lista.").text.split('\n')

def agente_escreve_capitulo(titulo, sinopse, contexto):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"Escreva o capítulo '{titulo}' (aprox 400-500 palavras) em Inglês baseado em '{sinopse}'. Contexto anterior: {contexto[-500:] if contexto else ''}"
    return model.generate_content(prompt).text

def agente_tradutor(texto_en):
    model = genai.GenerativeModel('gemini-2.5-flash')
    return model.generate_content(f"Traduza para Português Brasileiro, mantendo o tom épico e a formatação Markdown:\n{texto_en}").text

# --- FUNÇÕES DE MÍDIA ---
def gerar_capa_simples(titulo, nicho):
    if not os.path.exists("temp"): os.makedirs("temp")
    img = Image.new('RGB', (1080, 1920), color=(15, 15, 25))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 70)
    except:
        font = ImageFont.load_default()
    d.text((50, 800), f"{nicho}\n\n{titulo}", fill=(255, 215, 0), font=font)
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
    asyncio.run(_tts_async(texto, voz, arquivo))
    return arquivo

def renderizar_video(audio_path, imagem_path, idioma, preview=False):
    audio = AudioFileClip(audio_path)
    if preview:
        audio = audio.subclip(0, 60) # Corta 1 min para teste
    
    img = ImageClip(imagem_path).set_duration(audio.duration)
    video = CompositeVideoClip([img]).set_audio(audio)
    
    output = f"video_final_{idioma}.mp4"
    video.write_videofile(output, fps=1, codec="libx264", audio_codec="aac")
    return output
