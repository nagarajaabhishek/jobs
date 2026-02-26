import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

test_models = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite-preview-02-05",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

def test_model(model_name):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": "Say 'OK' if you see this."}]}]
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"Model: {model_name:35} | Status: {r.status_code}")
        if r.status_code != 200:
            print(f"  -> Error: {r.text[:100]}")
        else:
            print(f"  -> Success!")
    except Exception as e:
        print(f"Model: {model_name:35} | Exception: {e}")

print("Testing Gemini Free Tier Model Availability...\n")
for m in test_models:
    test_model(m)
