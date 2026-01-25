import os
from dotenv import load_dotenv

# Cargar el archivo .env desde /config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path)

def get_gemini_api_key():
    api = os.getenv("GEMINI_API_KEY")
    if not api:
        raise ValueError("❌ No se encontró GEMINI_API_KEY en /config/.env")
    return api
