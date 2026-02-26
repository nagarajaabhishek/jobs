import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    r = requests.get(url)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        models = r.json().get("models", [])
        print("\nAvailable Models:")
        for m in models:
            print(f"- {m['name']} ({m['displayName']})")
    else:
        print(f"Error: {r.text}")
except Exception as e:
    print(f"Exception: {e}")
