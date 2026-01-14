import google.generativeai as genai
import json
import streamlit as st

# --- 1. SINOPSE ---
def agente_sinopse(tema, nicho, generos):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Role: Professional Screenwriter for {nicho}.
    Task: Create a thrilling Synopsis for a 30-minute story (approx 8 chapters).
    Core Theme: "{tema}"
    Genres: {generos} (Mix these tones).
    Constraint: The story must have a clear beginning, middle, twist, and end.
    Output: Just the English synopsis text.
    """
    return model.generate_content(prompt).text

# --- 2. O ARQUITETO (PLANEJADOR) ---
def agente_planejador(sinopse, generos):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Role: Story Architect.
    Input Synopsis: "{sinopse}"
    Genres: {generos}
    
    Task: Break this story into exactly 8 Chapters.
    For EACH chapter, define:
    1. Title: Catchy and relevant.
    2. Plot Points: What EXACTLY happens? (Key events, clues found, actions).
    
    CRITICAL RULES:
    - Ensure linear progression. Do NOT repeat reveals.
    - If a clue is found in Ch3, do NOT find it again in Ch4.
    - Build tension until the climax in Ch 7.
    
    Output Format: JSON List of objects.
    Example:
    [
        {{"chapter_num": 1, "title": "The Arrival", "events": "Group arrives. They feel watched."}},
        {{"chapter_num": 2, "title": "First Signs", "events": "Power goes out. Strange noises."}}
    ]
    Return ONLY the JSON string.
    """
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception as e:
        print(f"Erro Planejador: {e}")
        return [{"title": f"Chapter {i}", "events": "Continue story."} for i in range(1,9)]

# --- 3. O ESCRITOR V2 ---
def agente_escreve_capitulo_v2(titulo, eventos_capitulo, sinopse, resumo_anterior, generos):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    ROLE: Chapter Writer.
    STORY SYNOPSIS: "{sinopse}"
    
    CURRENT TASK: Write Chapter "{titulo}".
    MANDATORY EVENTS TO COVER (The Plan):
    {eventos_capitulo}
    
    PREVIOUS CONTEXT (Summary):
    {resumo_anterior}
    
    INSTRUCTIONS:
    - Tone: {generos}.
    - Length: 400-500 words.
    - Language: English.
    - Style: Narrative documentary / Audio-book style.
    - CRITICAL: STICK TO THE PLAN. Do not advance to future events.
    """
    return model.generate_content(prompt).text

# --- 4. AUXILIARES ---
def agente_resumidor(texto_capitulo):
    model = genai.GenerativeModel('gemini-2.5-flash')
    return model.generate_content(f"Summarize the key events of this text in 3 sentences (English): {texto_capitulo}").text

def agente_visual(texto_capitulo):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Read this story chapter:
    "{texto_capitulo}"
    
    Task: Create 5 distinct image prompts to illustrate this chapter.
    Style: Cinematic, Realistic, 8k, Detailed environment, Wide shot.
    Output: Return ONLY the 5 prompts separated by a pipe symbol (|).
    """
    try:
        response = model.generate_content(prompt)
        prompts = response.text.split('|')
        return [p.strip() for p in prompts if p.strip()]
    except:
        return ["Cinematic scene of the story, detailed, 8k"] * 5

def agente_tradutor(texto_en):
    model = genai.GenerativeModel('gemini-2.5-flash')
    return model.generate_content(f"Traduza para PT-BR, mantendo fielmente a formatação Markdown (## Títulos, etc):\n{texto_en}").text

# --- 5. O CRÍTICO (NOVO) ---
def agente_critico(texto_completo, generos):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    ATUE COMO: Editor Literário Sênior de {generos}.
    TAREFA: Critique esta história.
    TEXTO: "{texto_completo}"
    
    FOCO:
    1. Motivação do Vilão (É específica? Se for vaga, reclame).
    2. Final (É impactante? Sugira algo cruel/psicológico se for fraco).
    3. Clichês.
    
    SAÍDA: Lista de melhorias em Português.
    """
    return model.generate_content(prompt).text

# --- 6. O REESCRITOR (NOVO) ---
def agente_reescritor(texto_atual, critica, generos):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    ATUE COMO: Ghostwriter Especialista.
    TAREFA: Reescreva a história aplicando a crítica do Editor.
    
    HISTÓRIA ORIGINAL:
    "{texto_atual}"
    
    CRÍTICA DO EDITOR:
    "{critica}"
    
    INSTRUÇÕES:
    - Mantenha a estrutura de capítulos.
    - Corrija APENAS o que foi criticado (melhore a motivação, mude o final).
    - Mantenha o tom {generos}.
    - Saída: História completa reescrita em Português (Markdown).
    """
    # Aumentamos o limite para garantir texto longo
    return model.generate_content(prompt).text
