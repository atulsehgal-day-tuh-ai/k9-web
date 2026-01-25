import os
from google import genai

def test_gemini():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    prompt = "Dame 3 consejos de seguridad para personal que trabaja en minas subterráneas."
    
    print(f"🚀 Enviando consulta a Gemini 2.5 Flash...")
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    
    print("\n🤖 Respuesta de la IA:")
    print("-" * 30)
    print(response.text)

if __name__ == "__main__":
    test_gemini()
