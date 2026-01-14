import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import nest_asyncio
from datetime import datetime

# --- BIBLIOTECAS GOOGLE (HÍBRIDO) ---
import google.generativeai as genai_old  # Para Texto (Agentes de Escrita)
from google import genai as genai_new    # Para Imagem (Imagen 4 Fast)

nest_asyncio.apply()

# --- CONFIGURAÇÃO GLOBAL ---
def setup_api():
    """
    Configura todas as APIs necessárias (Firebase, Google Texto, Google Imagem).
    Retorna True se tudo estiver OK.
    """
    # 1. Configura Google Gemini (SDK Antigo - Texto)
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai_old.configure(api_key=api_key)
    except Exception as e:
        st.error(f"Erro na API Google (Texto): {e}")
        return False
    
    # 2. Testa Cliente Google (SDK Novo - Imagem)
    # Não precisa 'configurar' globalmente, mas testamos a criação do cliente
    try:
        client = genai_new.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"Erro na API Google (Imagem/Nova): {e}")
        return False

    # 3. Configura Firebase
    try:
        if not firebase_admin._apps:
            cred_dict = dict(st.secrets["firebase"])
            # Correção comum para quebras de linha em chaves privadas
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        return True
    except Exception as e:
        print(f"Erro Firebase: {e}")
        return False

# --- HELPER: NOVO CLIENTE DE IMAGEM ---
def get_novo_client_google():
    """Retorna uma instância do novo cliente para ser usada nos agentes."""
    try:
        return genai_new.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    except:
        return None

# --- SEGURANÇA ---
def verificar_senha():
    if st.session_state.get("password_correct", False):
        return True

    st.markdown("### 🔒 Acesso Restrito (Content Farm)")
    password_input = st.text_input("Senha de Acesso:", type="password")

    if st.button("Entrar"):
        try:
            senha_secreta = st.secrets["APP_PASSWORD"]
            if password_input == senha_secreta:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta")
        except KeyError:
            st.error("ERRO: Configure APP_PASSWORD no secrets.toml")
            st.stop()
    return False

# --- BANCO DE DADOS (FIREBASE) ---
def salvar_historia_db(nicho, tema, generos, texto_pt, texto_en, prompts_visuais):
    try:
        db = firestore.client()
        dados = {
            "nicho": nicho,
            "generos": generos,
            "tema": tema,
            "roteiro_pt": texto_pt,
            "roteiro_en": texto_en,
            "prompts": prompts_visuais,
            "data_criacao": datetime.now(),
            "status": "Roteiro Pronto"
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
