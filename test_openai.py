from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

print(f"Usando a chave API: {api_key[:10]}...{api_key[-5:]}")

client = OpenAI(api_key=api_key)

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente útil."},
            {"role": "user", "content": "Olá, tudo bem?"}
        ]
    )
    print("Conexão bem-sucedida!")
    print(f"Resposta: {response.choices[0].message.content}")
except Exception as e:
    print(f"Erro ao conectar: {e}") 