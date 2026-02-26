import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.llm_router import LLMRouter

def test_gemini_connectivity():
    print("\n--- Verifying Gemini Connectivity (v1beta) ---\n")
    router = LLMRouter()
    router.provider = "gemini" # Explicitly test Gemini
    
    text = router._generate_gemini("You are a helpful assistant.", "Say 'Gemini is Online' if you can hear me.")
    
    if text:
        print(f"Response: {text}")
        print("\n✅ Gemini API: SUCCESS")
    else:
        print("\n❌ Gemini API: FAILED (Check logs for error codes)")

if __name__ == "__main__":
    test_gemini_connectivity()
