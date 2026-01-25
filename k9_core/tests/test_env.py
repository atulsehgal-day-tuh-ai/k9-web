import sys
import os

# Agregar la carpeta raíz del proyecto al PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from config.settings import get_gemini_api_key


def test():
    print("API KEY:", get_gemini_api_key())

if __name__ == "__main__":
    test()
