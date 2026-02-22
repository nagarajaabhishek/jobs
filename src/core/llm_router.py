import os
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def get_evaluation_config():
    """Import here to avoid circular dependencies."""
    from src.core.config import get_evaluation_config
    return get_evaluation_config()


class LLMRouter:
    def __init__(self, model=None):
        """Initializes the evaluation engine: OpenRouter, Gemini, Ollama, or hybrid."""
        eval_cfg = get_evaluation_config()
        self.ollama_model = model or eval_cfg.get("ollama_model") or "qwen2.5:7b"
        self.provider = eval_cfg.get("provider", "hybrid").lower()
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        self.openrouter_model = eval_cfg.get("openrouter_model") or os.environ.get("OPENROUTER_MODEL") or "google/gemini-2.0-flash-exp:free"
        self._session = requests.Session()

    def _generate_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """Calls Gemini 1.5 Flash via REST API."""
        if not self.gemini_key:
            return ""
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": f"System: {system_prompt}\n\nUser: {user_prompt}"}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.95,
                "topK": 40,
                "maxOutputTokens": 1024,
            }
        }
        
        try:
            r = self._session.post(url, headers=headers, json=payload, timeout=15)
            r.raise_for_status()
            data = r.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print(f"  ⚠ Gemini API failed: {e}")
            return ""

    def _generate_openrouter(self, system_prompt: str, user_prompt: str) -> str:
        """Calls OpenRouter (unified API). One key, many models."""
        if not self.openrouter_key:
            return ""
        url = f"{OPENROUTER_BASE_URL}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openrouter_key}",
        }
        payload = {
            "model": self.openrouter_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
        }
        try:
            r = self._session.post(url, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()
            return (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
        except Exception as e:
            print(f"  ⚠ OpenRouter API failed: {e}")
            return ""

    def _generate_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """Calls local Ollama API."""
        strict_format_reminder = (
            "\n\nCRITICAL INSTRUCTION: You MUST output your response in STRICT Markdown format exactly as follows:\n\n"
            "**Recommended Resume**\n[One of: TPM, PO, BA, SM, Manager, GTM]\n\n"
            "**Match Type**\n- **[One of: For sure, Worth Trying, Ambitious, Maybe, Not at all]**\n\n"
            "**Reasoning**\n[Brief explanation of fit based on the 5+ skill overlap rule]\n\n"
            "**Skill Gap Summary**\n[Brief summary of truly missing skills]\n\n"
            "Apply Conviction Score: [0-100]\n\n"
            "Do not output any conversational text. Only the Markdown."
        )
        full_prompt = f"{system_prompt}\n\n{user_prompt}{strict_format_reminder}"

        try:
            r = self._session.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={"model": self.ollama_model, "prompt": full_prompt, "stream": False},
                timeout=120,
            )
            r.raise_for_status()
            return (r.json().get("response") or "").strip()
        except Exception as e:
            print(f"  ⚠ Ollama failed: {e}")
            return ""

    def generate_content(self, system_prompt: str, user_prompt: str) -> tuple[str, str]:
        """Generates content based on selected provider with smart fallbacks."""
        
        # 1. OpenRouter (Explicit)
        if self.provider == "openrouter":
            print(f"  -> Attempting OpenRouter ({self.openrouter_model})...")
            text = self._generate_openrouter(system_prompt, user_prompt)
            return (text, "OPENROUTER") if text else ("", "FAILED")

        # 2. Gemini (Explicit)
        if self.provider == "gemini":
            print(f"  -> Attempting Gemini 1.5 Flash (Cloud)...")
            text = self._generate_gemini(system_prompt, user_prompt)
            return (text, "GEMINI") if text else ("", "FAILED")

        # 3. Ollama (Explicit)
        if self.provider == "ollama":
            print(f"  -> Attempting {self.ollama_model} (Local Ollama)...")
            text = self._generate_ollama(system_prompt, user_prompt)
            return (text, "OLLAMA") if text else ("", "FAILED")

        # 4. Hybrid (Fallback Chain: OpenRouter -> Gemini -> Ollama)
        if self.openrouter_key:
            print(f"  -> Attempting OpenRouter ({self.openrouter_model}) (Primary)...")
            text = self._generate_openrouter(system_prompt, user_prompt)
            if text:
                return text, "OPENROUTER"
            print("  -> OpenRouter failed. Falling back to Gemini...")

        print(f"  -> Attempting Gemini 1.5 Flash...")
        text = self._generate_gemini(system_prompt, user_prompt)
        if text:
            return text, "GEMINI"
        
        print(f"  -> Gemini failed. Falling back to local {self.ollama_model}...")
        text = self._generate_ollama(system_prompt, user_prompt)
        return (text, "OLLAMA") if text else ("", "FAILED")

    def check_ollama_available(self):
        """Returns (True, '') if Ollama is reachable and model exists; else (False, error_message)."""
        try:
            r = self._session.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            r.raise_for_status()
            names = [m.get("name", "") for m in (r.json().get("models") or [])]
            if not any(self.ollama_model == n or n.startswith(self.ollama_model + ":") for n in names):
                return False, f"Model '{self.ollama_model}' not found."
            return True, ""
        except Exception as e:
            return False, f"Ollama unreachable: {e}"
