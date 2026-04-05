import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def generate_text(user_prompt, system_prompt="You are a helpful AI.", temperature=0.7, max_tokens=150):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens
    )

    return response.choices[0].message.content