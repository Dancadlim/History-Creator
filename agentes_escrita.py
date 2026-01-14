import json
import streamlit as st
import utils # Importa o utils para pegar o cliente
from google import genai

# Modelo de texto padrão (usando o Flash 1.5 ou 2.0 que é estável)
MODELO_TEXTO = "gemini-1.5-flash" 

def _gerar_texto(prompt, json_mode=False):
    """Função auxiliar para chamar a nova API"""
    client = utils.get_google_client()
    if not client: return "Erro: API Key inválida."
    
    config = {}
    if json_mode:
        config['response_mime_type'] = 'application/json'

    try:
        response = client.models.generate_content(
            model=MODELO_TEXTO,
            contents=prompt,
            config=config
        )
        return response.text
    except Exception as e:
        return f"Erro na geração: {e}"

# --- 1. SINOPSE ---
def agente_sinopse(tema, nicho, generos):
    prompt = f"""
    Role: Professional Screenwriter for {nicho}.
    Task: Create a thrilling Synopsis for a 30-minute story (approx 8 chapters).
    Core Theme: "{tema}"
    Genres: {generos} (Mix these tones).
    Constraint: The story must have a clear beginning, middle, twist, and end.
    Output: Just the English synopsis text.
    """
    return _gerar_texto(prompt)

# --- 2. PLANEJADOR ---
def agente_planejador(sinopse, generos):
    prompt = f"""
    Role: Story Architect.
    Input Synopsis: "{sinopse}"
    Genres: {generos}
    Task: Break this story into exactly 8 Chapters.
    Output Format: JSON List of objects [{{ "title": "...", "events": "..." }}].
    Return ONLY the JSON string.
    """
    try:
        texto_json = _gerar_texto(prompt, json_mode=True)
        return json.loads(texto_json)
    except:
        return [{"title": f"Chapter {i}", "events": "Continue story."} for i in range(1,9)]

# --- 3. ESCRITOR ---
def agente_escreve_capitulo_v2(titulo, eventos_capitulo, sinopse, resumo_anterior, generos):
    prompt = f"""
    ROLE: Chapter Writer.
    SYNOPSIS: "{sinopse}"
    TASK: Write Chapter "{titulo}".
    PLAN: {eventos_capitulo}
    PREVIOUS CONTEXT: {resumo_anterior}
    INSTRUCTIONS: Tone {generos}. Length 400-500 words. English. Narrative style.
    """
    return _gerar_texto(prompt)

# --- 4. AUXILIARES ---
def agente_resumidor(texto_capitulo):
    return _gerar_texto(f"Summarize this in 3 sentences (English): {texto_capitulo}")

def agente_visual(texto_capitulo):
    # Prompt Visual Refinado (Realismo)
    prompt = f"""
    Read this story chapter:
    "{texto_capitulo}"
    
    Task: Create 5 distinct image prompts.
    CRITICAL VISUAL STYLE:
    - PHOTREALISTIC, 8k resolution, Raw Photography style.
    - FILM LOOK: 35mm film grain, cinematic lighting.
    - TEXTURE: Detailed skin, dirt, dust.
    - NEGATIVE PROMPT: 3d render, cartoon, smooth skin, anime.
    
    Output: Return ONLY the 5 prompts separated by a pipe symbol (|).
    """
    try:
        resp = _gerar_texto(prompt)
        prompts = resp.split('|')
        return [p.strip() for p in prompts if p.strip()]
    except:
        return ["Cinematic dark scene, photorealistic, 8k"] * 5

def agente_tradutor(texto_en):
    return _gerar_texto(f"Traduza para PT-BR mantendo a formatação Markdown (## Titulos):\n{texto_en}")

# --- 5. CRÍTICO E REESCRITOR ---
def agente_critico(texto_completo, generos):
    prompt = f"""
    ATUE COMO: Editor Literário de {generos}.
    ANALISE: "{texto_completo}"
    CRITIQUE: Motivação do Vilão, Final e Clichês.
    SAÍDA: Lista de melhorias em Português.
    """
    return _gerar_texto(prompt)

def agente_reescritor(texto_atual, critica, generos):
    prompt = f"""
    ATUE COMO: Ghostwriter.
    TAREFA: Reescreva aplicando a crítica.
    ORIGINAL: "{texto_atual}"
    CRÍTICA: "{critica}"
    SAÍDA: História completa reescrita em Português (Markdown).
    """
    return _gerar_texto(prompt)
