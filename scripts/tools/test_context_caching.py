import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.core.llm_router import LLMRouter # type: ignore

def test_caching():
    router = LLMRouter()
    
    system_prompt = "You are a helpful assistant. Here is a massive context: " + "A" * 5000 # ~5k tokens
    user_prompt = "Tell me a joke."
    
    print("--- FIRST CALL (Should create cache) ---")
    start = time.time()
    res1, engine1 = router.generate_content(system_prompt, user_prompt)
    print(f"Time: {time.time() - start:.2f}s")
    print(f"Response: {res1[:50]}...")
    
    print("\n--- SECOND CALL (Should hit cache) ---")
    start = time.time()
    res2, engine2 = router.generate_content(system_prompt, "Tell me another joke.")
    print(f"Time: {time.time() - start:.2f}s")
    print(f"Response: {res2[:50]}...")

if __name__ == "__main__":
    import time
    test_caching()
