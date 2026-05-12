import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
try:
    response = client.chat.completions.create(
        model="gpt-5.5",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=5
    )
    print("API key is valid:", response.choices[0].message.content)
except Exception as e:
    print("API error:", e)