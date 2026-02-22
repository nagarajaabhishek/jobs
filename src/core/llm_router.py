import os
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")


class LLMRouter:
    def __init__(self):
        """Initializes the Ollama-only evaluation engine (HTTP API, no subprocess per call)."""
        self.ollama_model = "llama3.2"
        self._session = requests.Session()

    def generate_content(self, system_prompt: str, user_prompt: str) -> tuple[str, str]:
        """Generates content using local Ollama via HTTP API (reuses connection, no process spawn)."""
        strict_format_reminder = (
            "\n\nCRITICAL INSTRUCTION: You MUST output your response in STRICT Markdown format exactly as follows:\n\n"
            "**Recommended Resume**\n[One of: TPM, PO, BA, SM, Manager, GTM]\n\n"
            "**Match Type**\n- **[One of: For sure, Worth Trying, Ambitious, Maybe, Not at all]**\n\n"
            "**Reasoning**\n[Brief explanation of fit based on the 5+ skill overlap rule]\n\n"
            "**Skill Gap Summary**\n[Brief summary of truly missing skills]\n\n"
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
            data = r.json()
            text = (data.get("response") or "").strip()
            return (text, "OLLAMA") if text else ("", "FAILED")
        except Exception as e:
            print(f"  -> Ollama request failed: {e}")
            return "", "FAILED"
