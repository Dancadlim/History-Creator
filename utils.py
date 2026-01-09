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

# Corrige conflito async do Streamlit
nest_asyncio.apply()

# Configura API
def setup_api():
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        return True
    except:
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

# --- FUNÇÕES AUXILIARES DE FONTE ---
def baixar_fonte():
    """Baixa a fonte Roboto-Black (Bem grossa) do Google"""
    font_path = "Roboto-Black.ttf"
    if not os.path.exists(font_path):
        print("Baixando fonte nova...")
        url = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Black.ttf"
        r = requests.get(url, allow_redirects=True)
        open(font_path, 'wb').write(r.content)
    return font_path

# --- FUNÇÕES DE MÍDIA ---
def gerar_capa_simples(titulo, nicho):
    if not os.path.exists("temp"): os.makedirs("temp")
    
    # 1. Fundo Azul Meia-Noite (Melhor que preto puro)
    img = Image.new('RGB', (1080, 1920), color=(10, 20, 50))
    d = ImageDraw.Draw(img)
    
    # 2. Fonte Gigante
    try:
        font_file = baixar_fonte()
        # Tamanho 90 para o Título (Bem Grande)
        font_titulo = ImageFont.truetype(font_file, 90) 
        # Tamanho 50 para o Nicho
        font_nicho = ImageFont.truetype(font_file, 50)  
    except Exception as e:
        print(f"Erro fonte: {e}")
        font_titulo = ImageFont.load_default()
        font_nicho = ImageFont.load_default()
    
    # 3. Formatação do Texto (Quebra de linha)
    # Quebra o título se ele for muito longo
    titulo_formatado = "\n".join(textwrap.wrap(titulo, width=15))
    
    # 4. Desenhar na tela
    # Nicho (Cinza claro)
    d.text((100, 600), nicho.upper(), fill=(200, 200, 200), font=font_nicho)
    
    # Título (Amarelo Ouro)
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
    
    # Remove markdown para não ser lido
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
