import os
import edge_tts
import asyncio
from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from PIL import Image
import io
import streamlit as st
# Importação da nova biblioteca oficial do Google
from google import genai
from google.genai import types

# --- CONFIGURAÇÃO DO CLIENTE GOOGLE (NOVA LIB) ---
try:
    # Tenta pegar a chave dos segredos
    api_key = st.secrets["GOOGLE_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception as e:
    print(f"Erro ao configurar Client GenAI: {e}")
    client = None

# --- ÁUDIO (TTS) ---
async def _tts_async(texto, voz, arquivo):
    communicate = edge_tts.Communicate(texto, voz)
    await communicate.save(arquivo)

def gerar_audio(texto, idioma, titulo):
    if not os.path.exists("temp"): os.makedirs("temp")
    voz = "pt-BR-AntonioNeural" if idioma == "pt" else "en-US-ChristopherNeural"
    arquivo = f"temp/audio_{idioma}.mp3"
    
    # Limpeza para evitar ler formatação
    texto_limpo = texto.replace("##", "").replace("**", "").replace("*", "")
    texto_final = f"{titulo}.\n\n{texto_limpo}"
    
    try:
        asyncio.run(_tts_async(texto_final, voz, arquivo))
        return arquivo
    except Exception as e:
        print(f"Erro TTS: {e}")
        return None

# --- IMAGEM REAL (IMAGEN 4 FAST) ---
def gerar_imagem_ia(prompt, nome_arquivo):
    if not os.path.exists("temp"): os.makedirs("temp")
    caminho_final = f"temp/{nome_arquivo}.png"
    
    # Cache: Se já existe, não gasta dinheiro gerando de novo
    if os.path.exists(caminho_final): return caminho_final

    if not client:
        print("Erro crítico: Cliente GenAI não inicializado.")
        return None

    try:
        print(f"🎨 Gerando (Imagen 4 Fast): {nome_arquivo}...")
        
        # Chamada para o Imagen 4 Fast (Econômico e Potente)
        response = client.models.generate_images(
            model='imagen-4.0-fast-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9", # Horizontal (YouTube/Cinema)
                safety_filter_level="block_low_and_above" # Filtro exigido pela API
            )
        )
        
        # Extração Segura da Imagem (Bytes -> PIL)
        generated_image = response.generated_images[0].image
        
        if isinstance(generated_image, types.Image):
            image_bytes = generated_image.image_bytes
            pil_image = Image.open(io.BytesIO(image_bytes))
            pil_image.save(caminho_final)
        else:
            # Fallback se a API mudar o tipo de retorno
            generated_image.save(caminho_final)
            
        return caminho_final

    except Exception as e:
        print(f"❌ Erro Imagem ({nome_arquivo}): {e}")
        
        # Fallback de Emergência (Gera imagem preta para não travar o vídeo)
        try:
            img = Image.new('RGB', (1920, 1080), color=(10, 10, 10))
            img.save(caminho_final)
            return caminho_final
        except:
            return None

# --- VÍDEO (RENDERIZAÇÃO COM ZOOM) ---
def renderizar_video_com_imagens(audio_path, lista_imagens, idioma):
    if not os.path.exists(audio_path): return None
    
    audio = AudioFileClip(audio_path)
    duracao_total = audio.duration
    
    if not lista_imagens: return None
    tempo_por_imagem = duracao_total / len(lista_imagens)
    
    clips = []
    for img_path in lista_imagens:
        try:
            clip = ImageClip(img_path).set_duration(tempo_por_imagem).set_position('center')
            
            # Efeito Ken Burns Suave (Zoom In de 4% ao longo do clipe)
            clip = clip.resize(lambda t: 1 + 0.04*t) 
            
            clips.append(clip)
        except Exception as e:
            print(f"Erro clip {img_path}: {e}")
            continue
            
    if not clips: return None

    video_final = concatenate_videoclips(clips, method="compose")
    video_final = video_final.set_audio(audio)
    
    output = f"video_final_{idioma}.mp4"
    
    # Preset 'ultrafast' para testes rápidos. Use 'medium' para qualidade final.
    video_final.write_videofile(
        output, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac", 
        preset="ultrafast",
        threads=4
    )
    return output
