import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful AI research assistant."
        },
        {
            "role": "user",
            "content": "Explain RAG in simple English."
        }
    ],
    temperature=0.2
)

print(response.choices[0].message.content)