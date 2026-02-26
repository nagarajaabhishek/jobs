import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def get_evaluation_config():
    """Import here to avoid circular dependencies."""
    from src.core.config import get_evaluation_config
    return get_evaluation_config()


class LLMRouter:
    def __init__(self, model=None):
        """Initializes the evaluation engine: OpenRouter or Gemini."""
        eval_cfg = get_evaluation_config()
        self.provider = eval_cfg.get("provider", "gemini").lower()
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        self.openrouter_model = eval_cfg.get("openrouter_model") or os.environ.get("OPENROUTER_MODEL") or "google/gemini-2.0-flash-exp:free"
        self._session = requests.Session()

    def _generate_gemini(self, system_prompt: str, user_prompt: str, formatting_instruction: str = None, model: str = None) -> str:
        """Calls Gemini 1.5 Pro/Flash via REST API."""
        if not self.gemini_key:
            print("  ⚠ Gemini API key not found in environment.")
            return ""
        
        # Use provided model or fallback to config
        model_name = model
        if not model_name:
            eval_cfg = get_evaluation_config()
            model_name = eval_cfg.get("gemini_model") or "gemini-1.5-pro-latest"
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.gemini_key}"
        headers = {"Content-Type": "application/json"}
        
        full_user_prompt = user_prompt
        if formatting_instruction:
            full_user_prompt += f"\n\n{formatting_instruction}"
            
        payload = {
            "contents": [{
                "parts": [{"text": f"System: {system_prompt}\n\nUser: {full_user_prompt}"}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.95,
                "topK": 40,
                "maxOutputTokens": 2048,
            }
        }
        
        try:
            import time
            max_retries = 5
            backoff = 3
            
            # Mandatory 1s delay to respect free tier RPM
            time.sleep(1)
            
            for attempt in range(max_retries):
                r = self._session.post(url, headers=headers, json=payload, timeout=60)
                
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
                
                first_candidate = candidates[0] or {}
                content = first_candidate.get("content", {})
                parts = content.get("parts", [])
                if not parts:
                    return ""
                    
                return parts[0].get("text", "").strip()
            
            print(f"  ⚠ Gemini API failed after {max_retries} retries (Rate Limited).")
            return ""
        except Exception as e:
            print(f"  ⚠ Gemini API failed: {e}")
            return ""

    def _generate_openrouter(self, system_prompt: str, user_prompt: str, formatting_instruction: str = None) -> str:
        """Calls OpenRouter (unified API). One key, many models."""
        if not self.openrouter_key:
            return ""
        url = f"{OPENROUTER_BASE_URL}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openrouter_key}",
        }
        
        full_user_prompt = user_prompt
        if formatting_instruction:
            full_user_prompt += f"\n\n{formatting_instruction}"
            
        payload = {
            "model": self.openrouter_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 2048,
        }
        try:
            r = self._session.post(url, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            choices = data.get("choices", [])
            if not choices:
                return ""
                
            first_choice = choices[0] or {}
            message = first_choice.get("message", {})
            return message.get("content", "").strip()
        except Exception as e:
            print(f"  ⚠ OpenRouter API failed: {e}")
            return ""

    def generate_content(self, system_prompt: str, user_prompt: str, formatting_instruction: str = None, model: str = None) -> tuple[str, str]:
        """Generates content using the configured cloud provider (Gemini or OpenRouter)."""
        
        # 1. Try Gemini if configured (Primary)
        if self.provider == "gemini":
            print(f"  -> Generating with Gemini...")
            text = self._generate_gemini(system_prompt, user_prompt, formatting_instruction=formatting_instruction, model=model)
            if text:
                return text, "GEMINI"
            
        # 2. Try OpenRouter if configured
        if self.provider == "openrouter":
            print(f"  -> Generating with OpenRouter ({self.openrouter_model})...")
            text = self._generate_openrouter(system_prompt, user_prompt, formatting_instruction=formatting_instruction)
            if text:
                return text, "OPENROUTER"

        # 3. Fail if no primary works
        print("  ⚠ No cloud-based LLM response received.")
        return "", "FAILED"
