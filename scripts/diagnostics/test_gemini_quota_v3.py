import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

test_cases = [
    ("v1beta", "gemini-2.0-flash"),
    ("v1beta", "gemini-2.5-flash-lite"),
    ("v1", "gemini-1.5-flash"),
    ("v1", "gemini-1.5-pro"),
    ("v1beta", "gemini-1.5-flash"),
    ("v1beta", "gemini-1.5-pro"),
]

def test_model(version, model_name):
    url = f"https://generativelanguage.googleapis.com/{version}/models/{model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": "Say 'OK' if you see this."}]}]
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"[{version}] Model: {model_name:25} | Status: {r.status_code}")
        if r.status_code != 200:
            print(f"  -> Error: {r.text[:200]}")
        else:
            print(f"  -> Success!")
    except Exception as e:
        print(f"[{version}] Model: {model_name:25} | Exception: {e}")

print("Testing Gemini Unified API Versions and Models...\n")
for v, m in test_cases:
    test_model(v, m)
