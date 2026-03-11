import os
import hashlib
import json
import time
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import requests # type: ignore
from dotenv import load_dotenv # type: ignore
from typing import Any, Dict, List, Tuple

load_dotenv()

def get_evaluation_config():
    """Import here to avoid circular dependencies."""
    from src.core.config import get_evaluation_config # type: ignore
    return get_evaluation_config()


class LLMRouter:
    def __init__(self, model=None):
        """Initializes the Gemini evaluation engine."""
        self.provider = "gemini"
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        
        # Robust load-retry if key is missing (likely due to module-load order/cwd issues)
        if not self.gemini_key:
            from dotenv import load_dotenv # type: ignore
            load_dotenv()
            self.gemini_key = os.environ.get("GEMINI_API_KEY")
            
        self._session = requests.Session()
        self.cache_registry_path = "data/gemini_context_caches.json"
        self._cache_registry: Dict[str, Any] = self._load_cache_registry()

    def _load_cache_registry(self):
        """Loads existing cache IDs from disk."""
        if os.path.exists(self.cache_registry_path):
            try:
                with open(self.cache_registry_path, "r") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_cache_registry(self):
        """Saves current cache IDs to disk."""
        try:
            os.makedirs(os.path.dirname(self.cache_registry_path), exist_ok=True)
            with open(self.cache_registry_path, "w") as f:
                json.dump(self._cache_registry, f, indent=2)
        except:
            pass

    def _get_or_create_cache(self, system_prompt: str, model_name: str) -> str | None:
        """
        Gemini Context Caching.
        Hashes the system_prompt. If a valid cache exists, returns its ID.
        Otherwise, creates a new one and returns the ID.
        """
        if not self.gemini_key: return None
        
        # 1. Clean model name for caching API
        clean_model = model_name
        if not clean_model.startswith("models/"):
            clean_model = f"models/{clean_model}"
            
        # 2. Hash system_prompt (the common context)
        content_hash = hashlib.sha256(system_prompt.encode()).hexdigest()
        
        # 3. Check registry for existing cache
        cached = self._cache_registry.get(content_hash)
        if cached:
            # Check if it was for the same model
            if cached.get("model") == clean_model:
                # Add a buffer for TTL checks if we had timestamps, 
                # but for now we'll attempt to use it and fallback on failure.
                return cached.get("name")
            
        # 4. Create new Context Cache if context is massive enough (>1024 tokens estimate)
        # We assume common contexts in this pipeline are always worth caching.
        url = f"https://generativelanguage.googleapis.com/v1beta/cachedContents?key={self.gemini_key}"
        payload = {
            "model": clean_model,
            "contents": [{"parts": [{"text": system_prompt}], "role": "user"}],
            "ttl": "3600s" # 1 hour TTL
        }
        
        try:
            r = self._session.post(url, json=payload, timeout=30)
            if r.status_code == 200:
                data = r.json()
                cache_name = data.get("name")
                if cache_name:
                    data["model"] = clean_model # Store model bound to cache
                    self._cache_registry[content_hash] = data
                    self._save_cache_registry()
                    print(f"  ✨ Created new Gemini context cache: {cache_name}")
                    return cache_name
        except Exception as e:
            print(f"  ⚠ Failed to create Gemini context cache: {e}")
            
        return None

    def _generate_gemini(self, system_prompt: str, user_prompt: str, formatting_instruction: str | None = None, model: str | None = None) -> str:
        """Calls Gemini 1.5 Pro/Flash via REST API."""
        if not self.gemini_key:
            print("  ⚠ Gemini API key not found in environment.")
            return ""
        
        # Use provided model or fallback to config
        model_name = model
        if not model_name:
            eval_cfg = get_evaluation_config()
            model_name = eval_cfg.get("gemini_model") or "gemini-1.5-pro-latest"
        
        # Try to use Caching
        cache_name = self._get_or_create_cache(system_prompt, model_name)
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.gemini_key}"
        headers = {"Content-Type": "application/json"}
        
        full_user_prompt = user_prompt
        if formatting_instruction:
            full_user_prompt += f"\n\n{formatting_instruction}"
        
        # Build Payload
        from typing import Any
        payload: Any = {
            "contents": [{
                "parts": [{"text": full_user_prompt}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.95,
                "topK": 40,
                "maxOutputTokens": 2048,
            }
        }
        
        # If cache exists, link it. Else, prepend system prompt to message.
        if cache_name:
            payload["cachedContent"] = cache_name # type: ignore
        else:
            payload["contents"][0]["parts"].insert(0, {"text": f"System Instruction:\n{system_prompt}\n\nTask:\n"}) # type: ignore
            
        try:
            max_retries = 3
            backoff = 3
            
            # Delay to respect free tier RPM
            time.sleep(0.5)
            
            for attempt in range(max_retries):
                r = self._session.post(url, headers=headers, json=payload, timeout=60)
                
                # Handle expired cache (404/410)
                if r.status_code in (404, 410) and cache_name:
                    print("  ⚠ Context cache expired. Retrying without cache...")
                    # Remove from registry
                    self._cache_registry = {k: v for k, v in self._cache_registry.items() if (isinstance(v, dict) and v.get("name") != cache_name)}
                    self._save_cache_registry()
                    # Fallback payload update
                    payload.pop("cachedContent", None) # type: ignore
                    payload["contents"][0]["parts"].insert(0, {"text": f"System Instruction:\n{system_prompt}\n\nTask:\n"}) # type: ignore
                    continue
                
                if r.status_code == 429:
                    wait_time = backoff ** (attempt + 1)
                    print(f"  ⚠ Rate limited (429). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                    
                r.raise_for_status()
                data = r.json()
                
                candidates = data.get("candidates", [])
                if not candidates:
                    return ""
                
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if not parts:
                    return ""
                    
                return parts[0].get("text", "").strip()
            
            print(f"  ⚠ Gemini API failed after {max_retries} retries.")
            return ""
        except Exception as e:
            print(f"  ⚠ Gemini API failed: {e}")
            return ""

    def generate_content(self, system_prompt: str, user_prompt: str, formatting_instruction: str | None = None, model: str | None = None) -> tuple[str, str]:
        """Generates content using the configured Gemini API."""
        print(f"  -> Generating with Gemini (Context Caching Enabled)...")
        text = self._generate_gemini(system_prompt, user_prompt, formatting_instruction=formatting_instruction, model=model)
        if text:
            return text, "GEMINI"
        
        print("  ⚠ No valid response received from Gemini.")
        return "", "FAILED"
