from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",  # Replace with your actual key
)

def analyze_txt_content(text):
    try:
        completion = client.chat.completions.create(
    model="deepseek/deepseek-chat-v3-0324:free",
    messages=[
        {
            "role": "system",
            "content": "You are a financial assistant. Give a short budget summary and 2 suggestions only."
        },
        {
            "role": "user",
            "content": f"{text}"
        }
    ],
    max_tokens=600,  # Limits output tokens
    extra_headers={
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "FinTracker AI",
    }
)


        # Ensure response has .choices and content
        if completion and completion.choices and completion.choices[0].message:
            return completion.choices[0].message.content
        else:
            return "❌ AI Error: No valid response received from model."

    except Exception as e:
        return f"❌ AI Error: {str(e)}"


import hashlib
import json

def generate_data_hash(profile_data, expense_data):
    combined = {
        "profile": profile_data,
        "expenses": expense_data
    }
    raw = json.dumps(combined, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()
