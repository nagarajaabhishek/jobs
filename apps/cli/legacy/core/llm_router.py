import os
import re
import hashlib
import json
import time
import sys
from datetime import datetime, timezone
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import requests # type: ignore
from dotenv import load_dotenv # type: ignore
from typing import Any, Dict, List, Tuple

load_dotenv()

def get_evaluation_config():
    """Import here to avoid circular dependencies."""
    from apps.cli.legacy.core.config import get_evaluation_config # type: ignore
    return get_evaluation_config()


class LLMRouter:
    @staticmethod
    def _parse_google_rfc3339_utc(value: Any) -> datetime | None:
        """Parse Gemini API timestamp (RFC3339, often with sub-microsecond fractions)."""
        if not value or not isinstance(value, str):
            return None
        s = value.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            if "T" not in s:
                return None
            try:
                date_part, time_part = s.split("T", 1)
                tz = ""
                if "+" in time_part:
                    time_main, tz = time_part.rsplit("+", 1)
                    tz = "+" + tz
                else:
                    time_main = time_part
                if "." in time_main:
                    hhmmss, frac = time_main.split(".", 1)
                    frac = re.sub(r"[^\d]", "", frac)[:6]
                    if not frac:
                        frac = "0"
                    time_main = f"{hhmmss}.{frac}"
                rebuilt = f"{date_part}T{time_main}{tz}"
                dt = datetime.fromisoformat(rebuilt)
            except Exception:
                return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _registry_cache_expired(self, cached: dict) -> bool:
        exp_raw = cached.get("expireTime")
        if not exp_raw:
            return False
        exp = self._parse_google_rfc3339_utc(exp_raw)
        if exp is None:
            return False
        return datetime.now(timezone.utc) >= exp

    def __init__(self, model=None):
        """Initializes HTTP clients for evaluation.provider (gemini | openai | openrouter)."""
        try:
            self.provider = (get_evaluation_config().get("provider") or "gemini").strip().lower()
        except Exception:
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
        self._sticky_provider: str | None = None
        self._sticky_remaining_calls: int = 0
        self._gemini_fail_streak: int = 0
        self._openrouter_fail_streak: int = 0

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
        
        # 3. Check registry for existing cache (skip entries past expireTime — avoids 403 every call)
        cached = self._cache_registry.get(content_hash)
        if cached:
            if cached.get("model") == clean_model:
                if self._registry_cache_expired(cached):
                    del self._cache_registry[content_hash]
                    self._save_cache_registry()
                    print("  ℹ Gemini context cache TTL passed; will create a new cachedContent.")
                else:
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

    def _gemini_429_should_use_openai(self) -> bool:
        """
        If True, first Gemini HTTP 429 returns empty so generate_content runs OpenAI fallback immediately
        (avoids long exponential backoff on the same rate-limited endpoint).
        """
        eval_cfg = get_evaluation_config()
        if eval_cfg.get("gemini_429_fast_openai_fallback") is False:
            return False
        if not (os.environ.get("OPENAI_API_KEY") or "").strip():
            return False
        fb_raw = eval_cfg.get("fallback_provider")
        fb_env = os.environ.get("EVAL_FALLBACK_PROVIDER")
        fb = str(fb_raw if fb_raw is not None else fb_env or "").strip().lower().replace(" ", "_")
        if fb in ("none", "null", "off", "false", ""):
            return False
        if fb == "gemma":
            return False
        if "openai" in fb:
            return True
        if fb in ("chatgpt", "gpt"):
            return True
        return False

    def _openrouter_429_should_fast_fallback(self) -> bool:
        """If True, first OpenRouter HTTP 429 returns empty so we try openrouter_fallback_model immediately."""
        eval_cfg = get_evaluation_config()
        if eval_cfg.get("openrouter_fast_fallback") is False:
            return False
        fb_model = (eval_cfg.get("openrouter_fallback_model") or "").strip()
        if not fb_model:
            return False
        fb_raw = eval_cfg.get("fallback_provider")
        fb_env = os.environ.get("EVAL_FALLBACK_PROVIDER")
        prov_raw = str(fb_raw if fb_raw is not None else fb_env or "").strip().lower().replace(" ", "_")
        if prov_raw in ("none", "null", "off", "false"):
            return False
        if not self._openrouter_should_try_second_model(prov_raw):
            return False
        return True

    @staticmethod
    def _openrouter_should_try_second_model(fallback_norm: str) -> bool:
        fb = str(fallback_norm or "").strip().lower().replace(" ", "_")
        if fb in ("none", "null", "off", "false"):
            return False
        # Gemini/OpenAI fallback chain keys do not apply without those keys.
        if fb in (
            "openai_then_gemma",
            "openai_gemma",
            "gemini_openai_gemma",
            "openai+gemma",
            "openai",
            "chatgpt",
            "gpt",
            "gemma",
            "gemma_then_openai",
            "gemma+openai",
            "gemma_openai",
        ):
            return False
        return True

    def _openrouter_extra_headers(self) -> Dict[str, str]:
        eval_cfg = get_evaluation_config()
        h: Dict[str, str] = {}
        referer = (
            (eval_cfg.get("openrouter_site_url") or "").strip()
            or (os.environ.get("OPENROUTER_HTTP_REFERER") or "").strip()
        )
        title = (
            (eval_cfg.get("openrouter_app_name") or "").strip()
            or (os.environ.get("OPENROUTER_APP_NAME") or "").strip()
        )
        if referer:
            h["HTTP-Referer"] = referer
        if title:
            h["X-Title"] = title
        return h

    def _chat_completions(
        self,
        *,
        api_key: str,
        model: str,
        system_prompt: str,
        user_full: str,
        max_tokens: int,
        base_url: str | None = None,
        extra_headers: Dict[str, str] | None = None,
        fast_429_handoff: bool = False,
        log_label: str = "OpenAI",
    ) -> str:
        root = (base_url or "https://api.openai.com/v1").rstrip("/")
        url = f"{root}/chat/completions"
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if extra_headers:
            headers.update(extra_headers)
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_full},
            ],
            "temperature": 0.1,
            "max_tokens": max_tokens,
        }
        backoff = 3
        for attempt in range(4):
            try:
                r = self._session.post(url, headers=headers, json=payload, timeout=300)
                if r.status_code == 429:
                    if fast_429_handoff:
                        print(
                            f"  ⚠ {log_label} rate limited (429). Fast fallback to secondary model "
                            f"(openrouter_fast_fallback)."
                        )
                        return ""
                    wait_s = backoff ** attempt
                    print(f"  ⚠ {log_label} rate limited (429). Retrying in {wait_s}s...")
                    time.sleep(wait_s)
                    continue
                if r.status_code != 200:
                    try:
                        err = r.text[:600]
                    except Exception:
                        err = ""
                    print(f"  ⚠ {log_label} HTTP {r.status_code}: {err}")
                    return ""
                data = r.json()
                choices = data.get("choices") or []
                if not choices:
                    print(f"  ⚠ {log_label} returned no choices.")
                    return ""
                msg = choices[0].get("message") or {}
                return (msg.get("content") or "").strip()
            except Exception as e:
                print(f"  ⚠ {log_label} request failed: {e}")
                if attempt < 3:
                    time.sleep(backoff ** attempt)
                    continue
                return ""
        return ""

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
        
        # Context caching (optional). Stale cache IDs → 403; see retry below. Disable: GEMINI_USE_CONTEXT_CACHE=0
        use_cache = os.environ.get("GEMINI_USE_CONTEXT_CACHE", "1").strip().lower() not in (
            "0",
            "false",
            "no",
            "off",
        )
        cache_name = self._get_or_create_cache(system_prompt, model_name) if use_cache else None
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.gemini_key}"
        headers = {"Content-Type": "application/json"}
        
        full_user_prompt = user_prompt
        if formatting_instruction:
            full_user_prompt += f"\n\n{formatting_instruction}"
        
        # Build Payload
        from typing import Any
        # Batch eval can emit many large JSON objects; 2048 tokens truncates → NEEDS_REVIEW / parse failures.
        try:
            max_out = int(os.environ.get("GEMINI_MAX_OUTPUT_TOKENS", "8192"))
        except ValueError:
            max_out = 8192
        max_out = max(2048, min(max_out, 65536))

        payload: Any = {
            "contents": [{
                "parts": [{"text": full_user_prompt}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.95,
                "topK": 40,
                "maxOutputTokens": max_out,
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

            # Optional throttle (default 0.5s) for strict RPM limits; set GEMINI_REQUEST_DELAY_SEC=0 on paid tiers.
            try:
                req_delay = float(os.environ.get("GEMINI_REQUEST_DELAY_SEC", "0.5"))
            except ValueError:
                req_delay = 0.5
            if req_delay > 0:
                time.sleep(req_delay)
            
            for attempt in range(max_retries):
                r = self._session.post(url, headers=headers, json=payload, timeout=60)
                
                # Handle expired / invalid context cache (404/410/403 CachedContent)
                if r.status_code in (404, 410) and cache_name:
                    print("  ⚠ Context cache expired. Retrying without cache...")
                    # Remove from registry
                    self._cache_registry = {k: v for k, v in self._cache_registry.items() if (isinstance(v, dict) and v.get("name") != cache_name)}
                    self._save_cache_registry()
                    # Fallback payload update
                    payload.pop("cachedContent", None) # type: ignore
                    payload["contents"][0]["parts"].insert(0, {"text": f"System Instruction:\n{system_prompt}\n\nTask:\n"}) # type: ignore
                    cache_name = None
                    continue

                cache_in_flight = cache_name or payload.get("cachedContent")
                if r.status_code == 403 and cache_in_flight:
                    # Stale/expired cache ID or cache permission — retry without cachedContent.
                    print(
                        "  ⚠ Gemini 403 while using context cache. Retrying without cachedContent "
                        "(registry entry removed; set GEMINI_USE_CONTEXT_CACHE=0 to disable caching)."
                    )
                    dead_name = cache_in_flight
                    self._cache_registry = {
                        k: v
                        for k, v in self._cache_registry.items()
                        if not (isinstance(v, dict) and v.get("name") == dead_name)
                    }
                    self._save_cache_registry()
                    payload.pop("cachedContent", None) # type: ignore
                    if not any(
                        isinstance(p, dict)
                        and str(p.get("text", "")).startswith("System Instruction:")
                        for p in payload["contents"][0]["parts"]
                    ):
                        payload["contents"][0]["parts"].insert(
                            0,
                            {"text": f"System Instruction:\n{system_prompt}\n\nTask:\n"},
                        )  # type: ignore
                    cache_name = None
                    continue
                
                if r.status_code == 429:
                    if self._gemini_429_should_use_openai():
                        print(
                            "  ⚠ Gemini rate limited (429). Using OpenAI via fallback_provider "
                            "(gemini_429_fast_openai_fallback; set false to retry Gemini only)."
                        )
                        return ""
                    wait_time = backoff ** (attempt + 1)
                    print(f"  ⚠ Rate limited (429). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                    
                if r.status_code != 200:
                    try:
                        err_body = r.text[:800]
                    except Exception:
                        err_body = ""
                    print(f"  ⚠ Gemini HTTP {r.status_code}: {err_body}")
                    r.raise_for_status()

                data = r.json()

                candidates = data.get("candidates", [])
                if not candidates:
                    pf = data.get("promptFeedback") or data.get("prompt_feedback")
                    if pf:
                        print(f"  ⚠ Gemini returned no candidates. promptFeedback={pf}")
                    else:
                        print(f"  ⚠ Gemini returned no candidates. Response keys: {list(data.keys())}")
                    return ""

                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if not parts:
                    fr = candidates[0].get("finishReason") or candidates[0].get("finish_reason")
                    if fr:
                        print(f"  ⚠ Gemini candidate has no text parts. finishReason={fr}")
                    return ""

                return parts[0].get("text", "").strip()
            
            print(f"  ⚠ Gemini API failed after {max_retries} retries.")
            return ""
        except Exception as e:
            print(f"  ⚠ Gemini API failed: {e}")
            return ""

    def _generate_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        formatting_instruction: str | None = None,
        model: str | None = None,
    ) -> str:
        """OpenAI Chat Completions (ChatGPT-class models)."""
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            print("  ⚠ OPENAI_API_KEY not set; cannot call OpenAI.")
            return ""

        eval_cfg = get_evaluation_config()
        model_name = model or eval_cfg.get("openai_model") or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        try:
            max_out = int(os.environ.get("OPENAI_MAX_COMPLETION_TOKENS", "8192"))
        except ValueError:
            max_out = 8192
        max_out = max(1024, min(max_out, 16384))

        user_full = user_prompt
        if formatting_instruction:
            user_full = f"{user_prompt}\n\n{formatting_instruction}"

        return self._chat_completions(
            api_key=key,
            model=model_name,
            system_prompt=system_prompt,
            user_full=user_full,
            max_tokens=max_out,
            base_url=None,
            extra_headers=None,
            fast_429_handoff=False,
            log_label="OpenAI",
        )

    def generate_content(self, system_prompt: str, user_prompt: str, formatting_instruction: str | None = None, model: str | None = None) -> tuple[str, str]:
        """
        Primary model from evaluation.provider (gemini | openai | openrouter).
        Gemini: optional fallback_provider openai_then_gemma, openai, gemma, gemma_then_openai.
        OpenRouter: optional openrouter_fallback_model when fallback_provider is openrouter_fallback (or unset).
        """
        eval_cfg = get_evaluation_config()
        base_provider = (eval_cfg.get("provider") or "gemini").strip().lower()
        provider = base_provider
        stick_enabled = bool(eval_cfg.get("provider_stickiness_enabled", False))
        stick_failures = int(eval_cfg.get("provider_stickiness_failures", 2) or 2)
        stick_calls = int(eval_cfg.get("provider_stickiness_calls", 20) or 20)
        using_sticky = False
        openrouter_sticky_fallback = False
        if stick_enabled and self._sticky_provider and self._sticky_remaining_calls > 0:
            if self._sticky_provider == "openrouter_fallback" and base_provider == "openrouter":
                openrouter_sticky_fallback = True
                using_sticky = True
                print(
                    f"  -> Provider stickiness active: OpenRouter fallback model "
                    f"({self._sticky_remaining_calls} call(s) remaining)."
                )
            else:
                provider = self._sticky_provider
                using_sticky = True
                print(
                    f"  -> Provider stickiness active: {provider} "
                    f"({self._sticky_remaining_calls} call(s) remaining)."
                )
        fb_raw = eval_cfg.get("fallback_provider")
        fb_env = os.environ.get("EVAL_FALLBACK_PROVIDER")
        fallback = (fb_raw if fb_raw is not None else fb_env or "")
        fallback_norm = str(fallback).strip().lower().replace(" ", "_")
        fallback_explicitly_off = fallback_norm in ("none", "null", "off", "false")
        if fallback_norm in ("none", "null", "off", "false", ""):
            fallback_norm = ""

        if provider == "openrouter":
            or_key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
            if not or_key:
                from dotenv import load_dotenv  # type: ignore

                load_dotenv()
                or_key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
            if not or_key:
                print("  ⚠ OPENROUTER_API_KEY not set; cannot call OpenRouter.")
                return "", "FAILED"
            try:
                max_out = int(
                    os.environ.get("OPENROUTER_MAX_COMPLETION_TOKENS")
                    or os.environ.get("OPENAI_MAX_COMPLETION_TOKENS", "8192")
                )
            except ValueError:
                max_out = 8192
            max_out = max(1024, min(max_out, 16384))
            user_full = user_prompt
            if formatting_instruction:
                user_full = f"{user_prompt}\n\n{formatting_instruction}"
            base_or = (
                os.environ.get("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1"
            ).strip().rstrip("/")
            fb_model = (eval_cfg.get("openrouter_fallback_model") or "").strip()
            primary_or = (eval_cfg.get("openrouter_model") or "google/gemini-2.5-flash").strip()

            def _one_or(mn: str, *, fast_429: bool, label: str) -> str:
                return self._chat_completions(
                    api_key=or_key,
                    model=mn,
                    system_prompt=system_prompt,
                    user_full=user_full,
                    max_tokens=max_out,
                    base_url=base_or,
                    extra_headers=self._openrouter_extra_headers(),
                    fast_429_handoff=fast_429,
                    log_label=label,
                )

            if openrouter_sticky_fallback:
                if not fb_model:
                    print("  ⚠ OpenRouter stickiness active but openrouter_fallback_model is empty.")
                    self._sticky_remaining_calls = max(0, self._sticky_remaining_calls - 1)
                    if self._sticky_remaining_calls == 0:
                        self._sticky_provider = None
                    return "", "FAILED"
                print("  -> OpenRouter (sticky fallback model)...")
                text = _one_or(fb_model, fast_429=False, label="OpenRouter")
                self._sticky_remaining_calls = max(0, self._sticky_remaining_calls - 1)
                if self._sticky_remaining_calls == 0:
                    self._sticky_provider = None
                if text:
                    self._openrouter_fail_streak = 0
                    return text, "OPENROUTER_FALLBACK"
                print("  ⚠ No valid response from OpenRouter fallback (sticky).")
                return "", "FAILED"

            if not using_sticky:
                print("  -> OpenRouter primary...")
            model_name = (model or primary_or).strip()
            fast_429 = self._openrouter_429_should_fast_fallback()
            text = _one_or(model_name, fast_429=fast_429, label="OpenRouter")
            if text:
                self._openrouter_fail_streak = 0
                return text, "OPENROUTER"

            if (
                fb_model
                and not fallback_explicitly_off
                and self._openrouter_should_try_second_model(fallback_norm)
            ):
                print("  -> OpenRouter primary empty; trying openrouter_fallback_model...")
                text2 = _one_or(fb_model, fast_429=False, label="OpenRouter fallback")
                if text2:
                    self._openrouter_fail_streak = 0
                    return text2, "OPENROUTER_FALLBACK"

            self._openrouter_fail_streak += 1
            if (
                stick_enabled
                and stick_failures > 0
                and self._openrouter_fail_streak >= stick_failures
                and stick_calls > 0
                and fb_model
                and not fallback_explicitly_off
            ):
                self._sticky_provider = "openrouter_fallback"
                self._sticky_remaining_calls = stick_calls
                print(
                    f"  ⚠ OpenRouter primary failed {self._openrouter_fail_streak} time(s); "
                    f"activating fallback-model stickiness for {stick_calls} call(s)."
                )

            print("  ⚠ No valid response from OpenRouter.")
            return "", "FAILED"

        if provider == "openai":
            if not using_sticky:
                print("  -> Generating with OpenAI (primary)...")
            text = self._generate_openai(
                system_prompt, user_prompt, formatting_instruction=formatting_instruction, model=None
            )
            if using_sticky:
                self._sticky_remaining_calls = max(0, self._sticky_remaining_calls - 1)
                if self._sticky_remaining_calls == 0:
                    self._sticky_provider = None
            if text:
                return text, "OPENAI"
            print("  ⚠ No valid response received from OpenAI.")
            return "", "FAILED"

        cache_hint = ""
        if os.environ.get("GEMINI_USE_CONTEXT_CACHE", "1").strip().lower() not in ("0", "false", "no", "off"):
            cache_hint = " (context cache on)"
        print(f"  -> LLM: Gemini first{cache_hint} — each new batch starts here; OpenAI only if Gemini returns empty.")
        text = self._generate_gemini(
            system_prompt, user_prompt, formatting_instruction=formatting_instruction, model=model
        )
        if text:
            self._gemini_fail_streak = 0
            return text, "GEMINI"
        self._gemini_fail_streak += 1
        if (
            stick_enabled
            and stick_failures > 0
            and self._gemini_fail_streak >= stick_failures
            and stick_calls > 0
            and (os.environ.get("OPENAI_API_KEY") or "").strip()
        ):
            self._sticky_provider = "openai"
            self._sticky_remaining_calls = stick_calls
            print(
                f"  ⚠ Gemini failed {self._gemini_fail_streak} time(s); "
                f"activating OpenAI stickiness for {stick_calls} call(s)."
            )

        gemma_model = (
            eval_cfg.get("gemma_model")
            or os.environ.get("GEMINI_GEMMA_MODEL")
            or "gemma-4-31b-it"
        )

        def _try_hosted_gemma(reason: str) -> tuple[str, str] | None:
            print(
                f"  -> {reason} Trying hosted Gemma ({gemma_model}) on Gemini API "
                "(open weights; same GEMINI_API_KEY)..."
            )
            t = self._generate_gemini(
                system_prompt,
                user_prompt,
                formatting_instruction=formatting_instruction,
                model=gemma_model,
            )
            if t:
                return t, "GEMMA_FALLBACK"
            return None

        if fallback_norm == "gemma":
            out = _try_hosted_gemma("Primary model returned empty.")
            if out:
                return out

        elif fallback_norm in ("gemma_then_openai", "gemma+openai", "gemma_openai"):
            out = _try_hosted_gemma("Primary model returned empty.")
            if out:
                return out
            print("  -> Gemma returned empty; falling back to OpenAI (ChatGPT API)...")
            text = self._generate_openai(
                system_prompt, user_prompt, formatting_instruction=formatting_instruction, model=None
            )
            if text:
                return text, "OPENAI_FALLBACK"

        elif fallback_norm in (
            "openai_then_gemma",
            "openai_gemma",
            "gemini_openai_gemma",
            "openai+gemma",
        ):
            print("  -> Gemini unavailable or empty; falling back to OpenAI (ChatGPT API)...")
            text = self._generate_openai(
                system_prompt, user_prompt, formatting_instruction=formatting_instruction, model=None
            )
            if text:
                return text, "OPENAI_FALLBACK"
            out = _try_hosted_gemma("OpenAI returned empty.")
            if out:
                return out

        elif fallback_norm in ("openai", "chatgpt", "gpt"):
            print("  -> Gemini unavailable or empty; falling back to OpenAI (ChatGPT API)...")
            text = self._generate_openai(
                system_prompt, user_prompt, formatting_instruction=formatting_instruction, model=None
            )
            if text:
                return text, "OPENAI_FALLBACK"

        print("  ⚠ No valid response from Gemini or fallback.")
        return "", "FAILED"
