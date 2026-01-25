import sys
import os

# Añadimos rutas del proyecto
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from config.settings import get_gemini_api_key
from google import genai

def test_list_models():
    client = genai.Client(api_key=get_gemini_api_key())
    models = client.models.list()

    print("=== MODELOS DISPONIBLES EN GOOGLE GENAI ===")
    for m in models:
        print("-", m.name)

if __name__ == "__main__":
    test_list_models()
