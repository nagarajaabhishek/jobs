import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

test_models = [
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro-latest",
    "gemini-2.0-flash-lite-preview-02-05", # Trying exact ID from list? No, let's use the ones in list.
    "gemini-2.0-pro-exp-02-05"
]

def test_model(model_name):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": "OK"}]}]
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"Model: {model_name:35} | Status: {r.status_code}")
    except Exception as e:
        print(f"Model: {model_name:35} | Exception: {e}")

print("Testing available Gemini models...\n")
for m in test_models:
    test_model(m)
