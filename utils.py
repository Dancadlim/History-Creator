import google.generativeai as genai
import edge_tts
import asyncio
import nest_asyncio
from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip, TextClip, ColorClip
import os
import streamlit as st
import requests
import textwrap
import re
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json

# Corrige conflito async do Streamlit
nest_asyncio.apply()

# --- CONFIGURAÇÃO INICIAL ---
def setup_api():
    try:
        # Tenta pegar a chave do Secrets
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    except:
        return False
    
    # Firebase
    try:
        if not firebase_admin._apps:
            cred_dict = dict(st.secrets["firebase"])
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        return True
    except Exception as e:
        print(f"Erro Firebase: {e}")
        return False

# --- SEGURANÇA ---
def verificar_senha():
    if st.session_state.get("password_correct", False):
        return True

    st.markdown("### 🔒 Acesso Restrito")
    password_input = st.text_input("Digite a senha de acesso:", type="password")

    if st.button("Entrar"):
        try:
            senha_secreta = st.secrets["APP_PASSWORD"]
        except KeyError:
            st.error("ERRO: Configure APP_PASSWORD no secrets.toml (topo do arquivo).")
            st.stop()

        if password_input == senha_secreta:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ Senha incorreta")
    return False

# --- AGENTES DE TEXTO (INTELIGÊNCIA) ---

def agente_sinopse(tema, nicho, generos):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Role: Screenwriter for {nicho}.
    Task: Create a Synopsis (30 min story).
    Theme: "{tema}"
    Genres: {generos} (Mix them).
    Output: Just the English text.
    """
    return model.generate_content(prompt).text

def agente_titulos(sinopse):
    model = genai.GenerativeModel('gemini-2.5-flash')
    return model.generate_content(f"Synopsis: '{sinopse}'. Create 8 Chapter Titles in English. List only.").text.split('\n')

def agente_escreve_capitulo(titulo, sinopse, contexto, generos):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Write Chapter: "{titulo}"
    Synopsis: "{sinopse}"
    Context: {contexto[-500:] if contexto else 'Start'}
    Tone: {generos}.
    Length: 400 words. English. Documentary style.
    """
    return model.generate_content(prompt).text

def agente_tradutor(texto_en):
    model = genai.GenerativeModel('gemini-2.5-flash')
    return model.generate_content(f"Traduza para PT-BR (Markdown):\n{texto_en}").text

def agente_visual(texto_capitulo):
    """
    Lê o capítulo e cria prompts de imagem para cada bloco.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Read this story chapter:
    "{texto_capitulo}"
    
    Task: Create 5 distinct image prompts to illustrate this chapter.
    Style: Cinematic, Realistic, 8k, Detailed environment.
    Output: Return ONLY the 5 prompts separated by a pipe symbol (|).
    Example: Ancient king on throne | Army marching in desert | ...
    """
    try:
        response = model.generate_content(prompt)
        prompts = response.text.split('|')
        return [p.strip() for p in prompts if p.strip()]
    except:
        return ["Cinematic scene of the story, detailed, 8k"] * 5

# --- GERAÇÃO DE IMAGEM (NOVO) ---
def gerar_imagem_ia(prompt, nome_arquivo):
    """
    Usa o modelo Imagen 3 (via API Gemini) para gerar imagens.
    Nota: Se sua chave não tiver acesso ao Imagen, usaremos um placeholder.
    """
    if not os.path.exists("temp"): os.makedirs("temp")
    caminho_final = f"temp/{nome_arquivo}.png"
    
    # Se já existir, não gasta crédito (cache simples)
    if os.path.exists(caminho_final):
        return caminho_final

    try:
        # Tenta usar o modelo de imagem do Google
        # Dependendo da lib, pode ser 'imagen-3.0-generate-001' ou via 'gemini-pro-vision' reverso
        # Para simplificar no AI Studio, usamos o endpoint padrão se disponível.
        
        # MODELO CORRETO PARA IMAGEM (conforme documentação atual da lib preview)
        # Se der erro, ele cai no except e gera uma cor sólida (para não travar)
        model_img = genai.GenerativeModel('gemini-2.5-flash') 
        # ATENÇÃO: A API Python do Gemini para imagem ainda está em beta.
        # Se não funcionar nativo, o ideal é usar REST API ou DALL-E.
        # Vou colocar um "Placeholder" aqui para o teste de lógica, 
        # pois a geração de imagem requer uma chamada específica que varia pela versão da lib.
        
        # --- SIMULAÇÃO PARA TESTE DE FLUXO (ATÉ VOCÊ TESTAR A GERAÇÃO REAL) ---
        # Remova isso quando formos colocar a chamada real da API de imagem
        img = Image.new('RGB', (1080, 1920), color=(50, 50, 50))
        d = ImageDraw.Draw(img)
        d.text((100, 900), prompt[:50], fill=(255,255,255))
        img.save(caminho_final)
        return caminho_final
        # -----------------------------------------------------------------------

    except Exception as e:
        print(f"Erro Imagem IA: {e}")
        return None

# --- FIREBASE: SALVAR E ATUALIZAR ---
def salvar_historia_db(nicho, tema, generos, texto_pt, texto_en, prompts_visuais):
    try:
        db = firestore.client()
        dados = {
            "nicho": nicho,
            "generos": generos,
            "tema": tema,
            "roteiro_pt": texto_pt,
            "roteiro_en": texto_en,
            "prompts": prompts_visuais, # Lista de strings
            "data_criacao": datetime.now(),
            "status": "Roteiro Pronto" # Status Inicial
        }
        db.collection("historias").add(dados)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

def atualizar_status_historia(historia_id, novo_status):
    try:
        db = firestore.client()
        db.collection("historias").document(historia_id).update({"status": novo_status})
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar status: {e}")
        return False

# --- ÁUDIO E VÍDEO ---
async def _tts_async(texto, voz, arquivo):
    communicate = edge_tts.Communicate(texto, voz)
    await communicate.save(arquivo)

def gerar_audio(texto, idioma, titulo):
    if not os.path.exists("temp"): os.makedirs("temp")
    voz = "pt-BR-AntonioNeural" if idioma == "pt" else "en-US-ChristopherNeural"
    arquivo = f"temp/audio_{idioma}.mp3"
    
    # Limpeza para evitar que ele leia "Hashtag Hashtag Capitulo Um"
    texto_limpo = texto.replace("##", "").replace("**", "").replace("*", "")
    texto_final = f"{titulo}.\n\n{texto_limpo}"
    
    try:
        asyncio.run(_tts_async(texto_final, voz, arquivo))
        return arquivo
    except Exception as e:
        st.error(f"Erro TTS: {e}")
        return None

# --- RENDERIZAÇÃO (COM EFEITO KEN BURNS SIMPLES) ---
def create_zoom_clip(image_path, duration):
    """Zoom lento (Ken Burns)"""
    # Nota: Zoom complexo no MoviePy pode ser lento.
    # Vamos fazer estático primeiro para garantir que roda, depois ativamos o zoom.
    return ImageClip(image_path).set_duration(duration).set_position('center')

def renderizar_video_com_imagens(audio_path, lista_imagens, idioma):
    """
    Junta Áudio + Várias Imagens divididas igualmente pelo tempo
    """
    if not os.path.exists(audio_path): return None
    
    audio = AudioFileClip(audio_path)
    duracao_total = audio.duration
    
    # Tempo de cada imagem
    if not lista_imagens: return None
    tempo_por_imagem = duracao_total / len(lista_imagens)
    
    clips = []
    for i, img_path in enumerate(lista_imagens):
        # Aqui entra o Ken Burns depois
        clip = ImageClip(img_path).set_duration(tempo_por_imagem).set_position('center')
        
        # Adiciona legenda simples (Exemplo basico)
        # Para legenda sincronizada precisa de mais logica (whisper timestamp)
        # Vamos deixar sem legenda hoje para testar o fluxo de imagem primeiro
        
        clips.append(clip)
        
    # Junta tudo
    video = CompositeVideoClip([
        *clips # Desempacota a lista de clips
        # Aqui entraria o concatenate_videoclips se fosse sequencial
    ])
    
    # Como ImageClip não é sequencial nativo no Composite sem set_start, 
    # o jeito certo de fazer Slideshow é concatenate:
    from moviepy.editor import concatenate_videoclips
    video_final = concatenate_videoclips(clips, method="compose")
    video_final = video_final.set_audio(audio)
    
    output = f"video_final_{idioma}.mp4"
    video_final.write_videofile(output, fps=24, codec="libx264", audio_codec="aac", preset="ultrafast")
    return output

# --- CAPA SIMPLES (FALLBACK) ---
def gerar_capa_simples(titulo, nicho):
    # Mantivemos essa caso a IA falhe
    if not os.path.exists("temp"): os.makedirs("temp")
    img = Image.new('RGB', (1080, 1920), color=(10, 20, 50))
    d = ImageDraw.Draw(img)
    # ... (mesmo codigo de antes)
    path = "temp/capa_temp.png"
    img.save(path)
    return path
