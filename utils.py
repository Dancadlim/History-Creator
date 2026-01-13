import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import google.generativeai as genai
import nest_asyncio
from datetime import datetime

nest_asyncio.apply()

# --- CONFIGURAÇÃO GLOBAL ---
def setup_api():
    # 1. Configura Google Gemini (para todos os módulos usarem)
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    except:
        return False
    
    # 2. Configura Firebase
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
