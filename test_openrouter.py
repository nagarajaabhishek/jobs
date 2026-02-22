import os
from src.core.llm_router import LLMRouter

def test_openrouter():
    print("Testing OpenRouter Integration...")
    router = LLMRouter()
    
    # Force OpenRouter for testing
    router.provider = "openrouter"
    
    system_prompt = "You are a helpful assistant."
    user_prompt = "Say 'OpenRouter is active!' if you can hear me."
    
    print(f"Provider: {router.provider}")
    print(f"Model: {router.openrouter_model}")
    
    text, engine = router.generate_content(system_prompt, user_prompt)
    
    print(f"\nResponse Engine: {engine}")
    print(f"Response Text: {text}")
    
    if "OpenRouter is active" in text:
        print("\n✅ OpenRouter is working perfectly!")
    else:
        print("\n❌ OpenRouter test failed or returned unexpected text.")

if __name__ == "__main__":
    test_openrouter()
