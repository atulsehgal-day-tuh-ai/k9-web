import os
from google import genai

def main():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    print(f"{'MODELO':<40} | {'ACCIONES SOPORTADAS'}")
    print("-" * 80)

    for model in client.models.list():
        # Usamos el atributo que descubrimos en tu diagnóstico
        actions = ", ".join(model.supported_actions) if model.supported_actions else "N/A"
        
        # Filtramos para resaltar los modelos que generan contenido
        if "generateContent" in actions:
            print(f"✅ {model.name:<38} | {actions}")
        else:
            print(f"   {model.name:<38} | {actions}")

if __name__ == "__main__":
    main()