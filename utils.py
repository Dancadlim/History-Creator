import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import nest_asyncio
from datetime import datetime
# --- MUDANÇA: Apenas a nova biblioteca ---
from google import genai 

nest_asyncio.apply()

# --- CONFIGURAÇÃO GLOBAL ---
def setup_api():
    """
    Testa se as chaves do Google e Firebase estão funcionando.
    """
    # 1. Testa Google GenAI (Nova Lib)
    try:
        if "GOOGLE_API_KEY" not in st.secrets:
            return False
        # Apenas tenta instanciar para ver se a chave existe
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    except Exception as e:
        st.error(f"Erro na API Google: {e}")
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

# --- HELPER: ENTREGAR O CLIENTE ---
def get_google_client():
    """
    Retorna o cliente autenticado para os outros arquivos usarem.
    """
    try:
        return genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    except:
        return None

# --- SEGURANÇA (Igual) ---
def verificar_senha():
    if st.session_state.get("password_correct", False):
        return True

    st.markdown("### 🔒 Acesso Restrito")
    password_input = st.text_input("Senha:", type="password")

    if st.button("Entrar"):
        try:
            if password_input == st.secrets["APP_PASSWORD"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Senha incorreta")
        except:
            st.error("Configure APP_PASSWORD no secrets.")
            st.stop()
    return False

# --- FIREBASE (Igual) ---
def salvar_historia_db(nicho, tema, generos, texto_pt, texto_en, prompts_visuais):
    try:
        db = firestore.client()
        dados = {
            "nicho": nicho, "generos": generos, "tema": tema,
            "roteiro_pt": texto_pt, "roteiro_en": texto_en,
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
    except: return False
