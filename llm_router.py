import os
import time
import subprocess
from google import genai
from dotenv import load_dotenv

load_dotenv()

class LLMRouter:
    def __init__(self):
        """
        Initializes the 3-Tier LLM Evaluation Engine.
        Tier 1: Gemini 2.0 Flash (Free, Fast)
        Tier 2: OpenAI gpt-4o-mini (Paid, Reliable Fallback)
        Tier 3: Local Ollama llama3.2 (Free, Slow Local Fallback)
        """
        # Primary: Gemini
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if self.gemini_api_key:
            self.gemini_client = genai.Client(api_key=self.gemini_api_key)
            self.gemini_model = 'gemini-2.0-flash'
        else:
            self.gemini_client = None
            print("WARNING: No GEMINI_API_KEY found. Primary engine disabled.")

        # Secondary: OpenAI
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        if self.openai_api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI()
            except ImportError:
                self.openai_client = None
                print("WARNING: OpenAI SDK not installed. Secondary engine disabled.")
        else:
            self.openai_client = None
            
        # Tertiary: Ollama
        self.ollama_model = 'llama3.2'

    def generate_content(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> tuple[str, str]:
        """
        Routes the prompt through the 3-tier fallback engine.
        Returns a tuple: (generated_text, model_used)
        """
        
        # 1. TIER 1: GEMINI (Primary)
        if self.gemini_client:
            retry_count = 0
            while retry_count < max_retries:
                try:
                    from google.genai import types
                    response = self.gemini_client.models.generate_content(
                        model=self.gemini_model,
                        contents=user_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                        )
                    )
                    return response.text, "GEMINI"
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg:
                        wait_time = 45 * (retry_count + 1)
                        print(f"  -> Gemini Quota (429). Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        retry_count += 1
                    else:
                        print(f"  -> Gemini failed: {e}")
                        break
        
        print("  -> TIER 1 FAILED. Routing to Tier 2 (OpenAI)...")
        
        # Strip the massive 8k token USER PROFILES section to prevent free-tier API crashes and offline local model context overflows.
        import re
        short_user_prompt = re.sub(r"### USER PROFILES.*?### JOB POSTING", "### JOB POSTING", user_prompt, flags=re.DOTALL)
        
        # 2. TIER 2: OPENAI (Secondary Fallback)
        if self.openai_client:
            retry_count = 0
            while retry_count < max_retries:
                try:
                    completion = self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": short_user_prompt}
                        ]
                    )
                    time.sleep(2) # Prevent high-throughput limit breaking on OpenAI free tier
                    return completion.choices[0].message.content, "OPENAI"
                except Exception as e:
                    import openai
                    if isinstance(e, openai.RateLimitError) or "429" in str(e):
                        wait_time = 20 * (retry_count + 1)
                        print(f"  -> OpenAI Quota (429). Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        retry_count += 1
                    else:
                        print(f"  -> OpenAI failed: {e}")
                        break
        else:
            print("  -> OpenAI not configured. Skipping Tier 2...")
            
        print("  -> TIER 2 FAILED. Routing to Tier 3 (Local Ollama)...")

        # 3. TIER 3: OLLAMA (Local Tertiary Fallback)
        try:
            # Inject strict formatting reminder for smaller local models
            strict_format_reminder = "\n\nCRITICAL INSTRUCTION: You MUST output your response in STRICT Markdown format exactly as follows:\n\n**Recommended Resume**\n[One of: PM, PO, BA, SM, Manager, GTM]\n\n**Match Type**\n- **[One of: For sure, Worth Trying, Ambitious, Maybe, Not at all]**\n\n**Skill Gap Summary**\n[Brief summary of missing skills]\n\nDo not output any conversational text. Only the Markdown."
            full_prompt = f"{system_prompt}\n\n{short_user_prompt}{strict_format_reminder}"
            
            process = subprocess.Popen(
                ['ollama', 'run', self.ollama_model],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout_data, _ = process.communicate(input=full_prompt)
            if stdout_data:
                return stdout_data, "OLLAMA"
            else:
                return "", "FAILED"
        except Exception as e:
            print(f"  -> Local Ollama completely failed: {e}")
            return "", "FAILED"
