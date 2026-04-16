import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def build_prompt(batch_texts):
    joined_reviews = "\n\n".join(
        [f"{i+1}. {text}" for i, text in enumerate(batch_texts)]
    )

    return f"""
Anda menganalisa ulasan aplikasi.

Funtuk setiap ulasan, berikan dalam JSON STRICTLY DALAM BAHASA INDONEWSIA format berikut:

[
  {{
    "sentiment": "positive | neutral | negative",
    "issues": ["list of issues"],
    "summary": "short summary"
  }}
]

Reviews:
{joined_reviews}
"""

def analyze_batch(texts):
    prompt = build_prompt(texts)

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except:
        return [{"sentiment": None, "issues": [], "summary": None}] * len(texts)