import logging
import os
import re
import sys
import json
from datetime import datetime

# agents -> legacy -> cli -> apps -> repo root (so `from apps.cli...` works when run as __main__)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
import yaml # type: ignore
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient, normalize_job_url # type: ignore
from apps.cli.legacy.core.llm_router import LLMRouter # type: ignore
from apps.cli.legacy.core.config import get_evaluation_config, get_learning_config # type: ignore
from apps.cli.legacy.core.job_filters import passes_evaluation_prefilter # type: ignore
from apps.cli.legacy.core.schemas import JobEvaluationSchema # type: ignore
from apps.cli.legacy.core.learning_schemas import DecisionAudit # type: ignore
from apps.cli.legacy.core.score_calibrator import apply_calibration, _load_patterns # type: ignore

RESUME_AGENT_BASE_DIR = os.path.join("core_agents", "resume_agent", ".agent")
TPM_OVERLAY_PATH = os.path.join(RESUME_AGENT_BASE_DIR, "overlays", "tpm_product.yaml")
DEFAULT_ROLE_YAML_PATH = os.path.join(RESUME_AGENT_BASE_DIR, "data", "Abhishek", "role_product_ops.yaml")
INTERVIEW_STORY_BANK_MAX_CHARS = 4500

# Fallback when config not used
BATCH_EVAL_SIZE_DEFAULT = 3
SHEET_BATCH_SIZE_DEFAULT = 25


def build_evaluation_update(
    row_index: int,
    match_type: str,
    recommended: str,
    h1b: str,
    loc_ver: str,
    missing: str,
    final_score: int,
    reasoning: str,
    base_llm_score: Any = None,
    calibration_delta: int = 0,
    decision_audit_json: str = "",
    evidence_json: str = "",
) -> Tuple[Any, ...]:
    """Build 12-tuple for GoogleSheetsClient (extended evaluation row + evidence)."""
    bs = base_llm_score if base_llm_score is not None else final_score
    return (
        row_index,
        match_type,
        recommended,
        h1b,
        loc_ver,
        missing,
        final_score,
        reasoning,
        int(calibration_delta),
        str(decision_audit_json or ""),
        bs,
        str(evidence_json or ""),
    )


def _clip_jd_for_batch_prompt(jd_text: str, max_chars: int) -> str:
    """Shorten JD embedded in multi-job user prompts to reduce output truncation (NEEDS_REVIEW)."""
    if max_chars <= 0 or len(jd_text) <= max_chars:
        return jd_text
    return (
        jd_text[:max_chars]
        + "\n[...truncated in batch prompt for token limits; full JD is in local cache.]"
    )


def _repair_reasoning_json_newlines(json_str: str) -> str:
    """
    Models often emit multiline text inside "reasoning": "..." which breaks json.loads.
    Collapse raw newlines inside that one string value to spaces so the blob can parse.
    """
    m = re.search(r'"reasoning"\s*:\s*"', json_str)
    if not m:
        return json_str
    start = m.end()
    i = start
    while i < len(json_str):
        c = json_str[i]
        if c == "\\" and i + 1 < len(json_str):
            i += 2
            continue
        if c == '"':
            rest = json_str[i + 1 : i + 24].lstrip()
            if rest.startswith(",") or rest.startswith("}"):
                inner = json_str[start:i]
                if "\n" in inner or "\r" in inner:
                    fixed = (
                        inner.replace("\r\n", " ")
                        .replace("\n", " ")
                        .replace("\r", " ")
                    )
                    return json_str[:start] + fixed + json_str[i:]
                return json_str
        i += 1
    return json_str


def score_to_verdict(score: int) -> str:
    """Map Apply Conviction Score to tiered verdict. Single source of truth for tests and evaluate_all."""
    if score >= 85:
        return "🚀 Must-Apply"
    if score >= 70:
        return "✅ Strong Match"
    if score >= 60:
        return "⚡ Ambitious Match"
    if score >= 40:
        return "⚖️ Worth Considering"
    if score >= 20:
        return "📉 Low Priority"
    return "❌ No"


class JobEvaluator:
    def __init__(self):
        self.sheets_client = GoogleSheetsClient()
        self.llm = LLMRouter()
        self.prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts",
            "gemini_job_fit_analyst.md",
        )
        self.deep_packet_prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts",
            "deep_job_packet.md",
        )
        self.roles = sorted([
            "Product Manager (TPM)", "Product Owner (PO)", "Business Analyst (BA)", 
            "Scrum Master (SM)", "Manager", "Go-To Market (GTM)"
        ])
        
        # Load verified sponsors
        self.sponsors: Dict[str, str] = {}
        self.cache_updated = False
        self.sponsors_path = "data/sponsors.yaml"
        if os.path.exists(self.sponsors_path):
            with open(self.sponsors_path, "r") as f:
                self.sponsors = yaml.safe_load(f) or {}

        # Load Intelligence Caches
        self.skill_gaps_path = "data/skill_gap_frequency.yaml"
        self.skill_gaps = self._load_yaml_cache(self.skill_gaps_path)
        
        self.salary_benchmarks_path = "data/salary_benchmarks.yaml"
        self.salary_benchmarks = self._load_yaml_cache(self.salary_benchmarks_path)
        
        self.company_insights_path = "data/company_insights.yaml"
        self.company_insights = self._load_yaml_cache(self.company_insights_path)

        # Cache overlay + pillars for the role-aware judge
        self._tpm_overlay: Optional[Dict[str, Any]] = None
        self._content_pillars_md: Optional[str] = None
        self._judge_workflow_md: Optional[str] = None

        self.formatting_instruction = (
            "\n\nCRITICAL INSTRUCTION: You MUST output ONLY a valid JSON object matching the exact "
            "schema provided in the base prompt. DO NOT include any conversational text, explanations, "
            "or markdown formatting blocks (like ```json)."
        )

    def get_verified_sponsorship(self, company):
        """Checks if a company has a verified sponsorship history."""
        # Sheets / pandas can surface empty cells as float NaN; normalize before .lower().
        if company is None:
            return "Unknown"
        try:
            c = str(company).strip()
        except Exception:
            return "Unknown"
        if not c or c.lower() in ("nan", "none", "nat"):
            return "Unknown"
        company = c
        # Exact match or partial match
        for key, val in self.sponsors.items():
            if key.lower() == company.lower() or key.lower() in company.lower():
                return val
        return "Not in verified database (LLM should estimate)"

    def get_strategic_priority(self, location):
        """Calculates a priority score based on location preferences."""
        loc = (location or "").lower()
        if "texas" in loc or "arlington" in loc or "dallas" in loc or "austin" in loc:
            return "HIGH (Texas Resident - Top Priority)"
        if "remote" in loc:
            return "MEDIUM-HIGH (Remote - Preferred)"
        if "dubai" in loc or "uae" in loc or "emirates" in loc:
            return "MEDIUM (Dubai Target)"
        return "STANDARD (On-site/Normal Priority)"

    def update_sponsorship_cache(self, company, status):
        """Updates the sponsorship cache if a definitive status is found."""
        if company is None or status is None:
            return
        if isinstance(company, float) and company != company:  # NaN from sheets
            return
        try:
            clean_company = str(company).strip()
        except Exception:
            return
        if not clean_company or clean_company.lower() in ("nan", "none", "nat"):
            return
        try:
            clean_status = str(status).strip()
        except Exception:
            return
        if not clean_status:
            return
        
        # We only cache definitive "Likely" or "Unlikely" status from the LLM
        # if the company isn't already verified with a strong record.
        if "Likely:" in clean_status or "Unlikely:" in clean_status:
            # Check if we already have it
            existing = self.sponsors.get(clean_company)
            if not existing or "LLM estimated" in str(existing) or "Not in verified database" in str(existing):
                label = "Sponsors" if "Likely:" in clean_status else "Does Not Sponsor"
                self.sponsors[clean_company] = f"{label} (Learned from JD)"
                self.cache_updated = True
                print(f"    ✨ Cached sponsorship for '{clean_company}': {label}")

    def save_sponsorship_cache(self):
        """Saves the cached sponsors back to YAML if updated."""
        if self.cache_updated:
            print("\nUpdating sponsorship cache (data/sponsors.yaml)...")
            try:
                with open(self.sponsors_path, "w") as f:
                    yaml.dump(self.sponsors, f, sort_keys=True)
                self.cache_updated = False
            except Exception as e:
                print(f"  ❌ Error saving sponsorship cache: {e}")

    def evaluate_single_job(self, url):
        """
        Evaluates a single job URL. Primarily used by the ADK orchestrator.
        """
        logging.info(f"Evaluating single job: {url}")
        
        # 1. Fetch JD
        jd_text = (self.sheets_client.get_jd_for_url(url) or "").strip()
        if not jd_text or jd_text.lower() == "none":
            return {"verdict": "⚠️ Missing JD", "score": 0, "reasoning": "Could not fetch JD."}
        
        # 2. Prepare Context
        sys_prompt = self.load_system_prompt()
        profiles_prompt = self.load_user_profiles()
        story_excerpt = self.load_interview_story_bank_excerpt()
        grounded_sys_prompt = (
            f"{sys_prompt}\n\n### USER PROFILE SUMMARY\n{profiles_prompt}{story_excerpt}"
        )
        
        # 3. Prepare Job Data (minimal)
        # In a single eval, we might not have the full job record if coming from ADK tool.
        # But we try to find it in the sheet if it exists.
        company = "Unknown"
        location = "United States"
        records, _ = self.sheets_client.get_new_jobs(limit=1000)
        for r in records:
            if normalize_job_url(r.get("Job Link", "")) == normalize_job_url(url):
                company = r.get("Company", "Unknown")
                location = r.get("Location", "United States")
                break
        
        sponsor_info = self.get_verified_sponsorship(company)
        priority = self.get_strategic_priority(location)
        overlap = self.count_skill_overlap(jd_text)
        
        user_prompt = (
            f"### JOB POSTING\n"
            f"URL: {url}\n"
            f"Company: {company}\n"
            f"Strategic Priority: {priority}\n"
            f"Verified Sponsorship History: {sponsor_info}\n"
            f"JD Content: {jd_text}\n[Pre-check: {overlap} skill overlap.]"
        )
        
        # 4. Generate
        eval_cfg = get_evaluation_config()
        eval_model = eval_cfg.get("gemini_model")
        
        raw_text, engine_used = self.llm.generate_content(
            grounded_sys_prompt, user_prompt, 
            formatting_instruction=self.formatting_instruction,
            model=eval_model
        )
        
        if engine_used == "FAILED":
            return {"verdict": "FAILED", "score": 0, "reasoning": "LLM failed."}
        
        # 5. Parse
        parsed = self.parse_evaluation(raw_text)
        match_type, rec, h1b, loc, missing, reasoning, salary, tech, score = parsed
        
        if score == 0:
            score = self._compute_fallback_score(jd_text, location)

        base_score = score
        learn_cfg = get_learning_config()
        title_guess = ""
        if learn_cfg.get("enabled", True):
            max_delta = int(learn_cfg.get("max_abs_delta", 15))
            pp = learn_cfg.get("patterns_path", "data/learned_patterns.yaml")
            ppath = pp if os.path.isabs(pp) else os.path.join(os.getcwd(), pp)
            patterns = _load_patterns(ppath)
            final_score, audit = apply_calibration(
                base_score,
                jd_text,
                title=title_guess,
                company=company,
                patterns=patterns,
                max_abs_delta=max_delta,
                cycle_id=os.environ.get("PIPELINE_CYCLE_ID", ""),
            )
        else:
            final_score = base_score
            audit = DecisionAudit(
                base_llm_score=base_score,
                calibration_delta=0,
                final_score=base_score,
                matched_patterns=[],
                cycle_id=os.environ.get("PIPELINE_CYCLE_ID", ""),
            )

        match_type = score_to_verdict(final_score)

        return {
            "verdict": match_type,
            "score": final_score,
            "base_llm_score": base_score,
            "calibration_delta": audit.calibration_delta,
            "decision_audit_json": audit.to_json(),
            "recommended_resume": rec,
            "h1b": h1b,
            "missing_skills": missing,
            "reasoning": reasoning,
            "salary": salary,
            "tech_stack": tech,
        }


    def _load_yaml_cache(self, path):
        """Helper to load YAML cache safely."""
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = yaml.safe_load(f)
                    return data if isinstance(data, dict) else {}
            except Exception:
                return {}
        return {}

    def update_intelligence_caches(self, job_data, eval_results):
        """Updates all intelligence caches based on evaluation findings."""
        company = job_data.get("Company")
        if not company: return
        
        self.cache_updated = True # Trigger global save
        
        # 1. Skill Gaps freq
        missing_str = eval_results.get("missing_skills", "")
        if missing_str and "N/A" not in missing_str:
            for skill in [s.strip() for s in missing_str.split(",") if s.strip()]:
                # Normalize skill name (lowercase, remove noise)
                norm_skill = skill.lower().replace("*", "").replace(".", "").strip()
                if norm_skill:
                    self.skill_gaps[norm_skill] = self.skill_gaps.get(norm_skill, 0) + 1
        
        # 2. Salary Benchmarks
        salary = eval_results.get("salary", "")
        if salary and "Not mentioned" not in salary:
            role = eval_results.get("recommended_resume", "Unknown PM")
            loc = job_data.get("Location", "Unknown")
            if role not in self.salary_benchmarks: self.salary_benchmarks[role] = {}
            # We store the latest observed range
            self.salary_benchmarks[role][loc] = salary
            
        # 3. Company Insights (Tech Stack)
        tech_stack = eval_results.get("tech_stack", "")
        if tech_stack and "Not mentioned" not in tech_stack:
            if company not in self.company_insights: 
                self.company_insights[company] = {"tech_stack": [], "sentiment": "Identified"}
            
            # Merge stacks
            current_stack = set(self.company_insights[company].get("tech_stack", []))
            new_techs = [t.strip() for t in tech_stack.split(",") if t.strip()]
            current_stack.update(new_techs)
            self.company_insights[company]["tech_stack"] = sorted(list(current_stack))

    def save_all_caches(self):
        """Atomically saves all intelligence caches."""
        if not self.cache_updated: return
        
        print("\nUpdating Intelligence Caches in data/...")
        caches = [
            (self.sponsors_path, self.sponsors),
            (self.skill_gaps_path, self.skill_gaps),
            (self.salary_benchmarks_path, self.salary_benchmarks),
            (self.company_insights_path, self.company_insights)
        ]
        
        for path, data in caches:
            try:
                with open(path, "w") as f:
                    yaml.dump(data, f, sort_keys=True)
            except Exception as e:
                print(f"  ❌ Error saving cache to {path}: {e}")
        
        self.cache_updated = False


    def passes_initial_filter(self, job):
        """
        Fast, rule-based filter to skip obviously bad jobs before sending to LLM.
        Uses shared rules from src.core.job_filters.
        Returns (True, "") if it passes, or (False, "Reason") if it fails.
        """
        return passes_evaluation_prefilter(job)

    def load_system_prompt(self):
        with open(self.prompt_path, 'r') as f:
            return f.read()

    def load_user_profiles(self):
        """Loads the highly compressed dense matrix for efficient LLM context."""
        matrix_path = os.environ.get("DENSE_MATRIX_PATH") or os.path.join(os.getcwd(), "data", "dense_master_matrix.json")
        try:
            with open(matrix_path, "r") as f:
                matrix_data = json.load(f)
                
            # Render a hyper-dense context block
            summary = "## CANDIDATE DENSE MATRIX (JSON CONTEXT)\n"
            summary += json.dumps(matrix_data, indent=2)
            
            # Append available roles for the output
            roles = [k for k in matrix_data.get("role_variants", {}).keys()]
            summary += f"\n\n### TARGET ROLES AVAILABLE\n{', '.join(roles)}"
            return summary
        except Exception as e:
            raise RuntimeError(
                "Dense profile missing/invalid. Evaluation must be grounded in the user's master context.\n"
                "Fix: ensure data/profiles/master_context.yaml exists, then run:\n"
                "  python3 apps/cli/scripts/tools/build_dense_matrix.py\n"
                f"Details: {e}"
            )

    def load_interview_story_bank_excerpt(self) -> str:
        """Optional STAR story bank (data/interview_story_bank.md) injected into the analyst prompt."""
        path = os.environ.get("INTERVIEW_STORY_BANK_PATH") or os.path.join(
            os.getcwd(), "data", "interview_story_bank.md"
        )
        if not os.path.isfile(path):
            return ""
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read().strip()
            if not text:
                return ""
            cap = int(os.environ.get("INTERVIEW_STORY_BANK_MAX_CHARS") or INTERVIEW_STORY_BANK_MAX_CHARS)
            if len(text) > cap:
                text = text[:cap] + "\n\n[... truncated for context window ...]"
            return (
                "\n\n### INTERVIEW STORY BANK EXCERPT (read-only; align hooks, do not invent facts)\n"
                + text
            )
        except OSError:
            return ""

    def _load_deep_packet_system_prompt(self) -> str:
        try:
            with open(self.deep_packet_prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except OSError:
            return ""

    def _run_deep_job_packet(
        self,
        job: Dict[str, Any],
        jd_text: str,
        final_score: int,
        reasoning: str,
        recommended_resume: str,
        h1b: str,
        evidence_json: str,
    ) -> str:
        """
        Optional second LLM pass: write data/deep_packets/<date>_r<row>.md.
        Returns relative path from cwd, empty if skipped, or ERROR:* for sheet visibility.
        """
        eval_cfg = get_evaluation_config()
        if not eval_cfg.get("deep_eval_enabled", False):
            return ""
        min_sc = int(eval_cfg.get("deep_eval_min_score", 90))
        if final_score < min_sc:
            return ""

        system_prompt = self._load_deep_packet_system_prompt()
        if not system_prompt.strip():
            return "ERROR: deep packet prompt missing"

        profiles = self.load_user_profiles()
        if len(profiles) > 14000:
            profiles = profiles[:14000] + "\n[... profile truncated ...]"

        company = job.get("Company") or ""
        title = job.get("Role Title") or ""
        jd_chunk = (jd_text or "")[:28000]

        user_prompt = (
            "### USER PROFILE SUMMARY (dense matrix excerpt)\n"
            f"{profiles}\n\n"
            "### PRIMARY EVALUATION (already completed — do not contradict)\n"
            f"Apply conviction (final): {final_score}\n"
            f"Recommended resume variant: {recommended_resume}\n"
            f"H1B sponsorship field: {h1b}\n"
            f"Reasoning:\n{reasoning}\n\n"
            "### STRUCTURED EVIDENCE JSON\n"
            f"{evidence_json or '{}'}\n\n"
            "### TARGET JOB\n"
            f"Title: {title}\nCompany: {company}\n\n### JOB DESCRIPTION\n{jd_chunk}"
        )

        eval_model = eval_cfg.get("gemini_model")
        raw, engine_used = self.llm.generate_content(
            system_prompt,
            user_prompt,
            formatting_instruction=self.formatting_instruction,
            model=eval_model,
        )
        if engine_used == "FAILED" or not (raw or "").strip():
            return "ERROR: deep packet LLM failed"

        text = raw.strip()
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return "ERROR: deep packet JSON not found"
        try:
            obj = json.loads(text[start : end + 1])
            md = (obj.get("markdown") or "").strip()
        except (json.JSONDecodeError, TypeError, AttributeError):
            return "ERROR: deep packet parse failed"
        if not md:
            return "ERROR: deep packet empty markdown"

        out_dir = os.path.join(os.getcwd(), "data", "deep_packets")
        os.makedirs(out_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        row_ix = int(job.get("_row_index", 0))
        fname = f"{date_str}_r{row_ix}.md"
        abs_path = os.path.join(out_dir, fname)
        try:
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(md)
        except OSError as e:
            return f"ERROR: write failed ({e})"
        return os.path.relpath(abs_path, os.getcwd())

    def _write_tailor_payload_json(
        self,
        job: Dict[str, Any],
        jd_text: str,
        final_score: int,
        recommended_resume: str,
        missing: str,
        evidence_json: str,
    ) -> str:
        """
        Optional JSON for external resume/PDF tooling (career-ops–style).
        Gated by config + score >= evaluation.tailor_min_score.
        Returns relative path or "".
        """
        eval_cfg = get_evaluation_config()
        tailor_min = int(eval_cfg.get("tailor_min_score", 90))
        if not eval_cfg.get("export_tailor_json", False) or final_score < tailor_min:
            return ""

        evidence_list: Any = []
        try:
            o = json.loads(evidence_json or "{}")
            if isinstance(o, dict):
                evidence_list = o.get("evidence") or []
        except (json.JSONDecodeError, TypeError):
            evidence_list = []

        gaps = [s.strip() for s in (missing or "").split(",") if s.strip()]
        job_link = job.get("Job Link") or job.get("url") or ""

        payload = {
            "exported_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "row_index": job.get("_row_index"),
            "job_link": job_link,
            "company": job.get("Company"),
            "role_title": job.get("Role Title"),
            "apply_conviction_score": final_score,
            "recommended_resume": recommended_resume,
            "skill_gaps": gaps,
            "jd_excerpt": (jd_text or "")[:12000],
            "evidence": evidence_list,
            "notes": "For LaTeX, Playwright/HTML PDF, or manual tailoring; verify before submit.",
        }

        out_dir = os.path.join(os.getcwd(), "data", "tailor_payloads")
        os.makedirs(out_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        row_ix = int(job.get("_row_index", 0))
        fname = f"{date_str}_row{row_ix}.json"
        abs_path = os.path.join(out_dir, fname)
        try:
            with open(abs_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except OSError:
            return ""
        rel = os.path.relpath(abs_path, os.getcwd())
        print(f"    📎 Tailor payload: {rel}")
        return rel

    def get_profile_skill_keywords(self):
        """Extract searchable skill keywords from the dense matrix for overlap counting."""
        keywords = set()
        matrix_path = os.path.join(os.getcwd(), "data", "dense_master_matrix.json")
        try:
            if not os.path.exists(matrix_path): 
                return keywords
                
            with open(matrix_path, "r") as f:
                matrix_data = json.load(f)
                
            # Extract from core skills across role variants
            for role_data in matrix_data.get("role_variants", {}).values():
                for skill_category_str in role_data.get("core_skills", []):
                    # Example format: "Product Management: Product Strategy, Roadmap..."
                    if ":" in skill_category_str:
                        skill_list_str = skill_category_str.split(":", 1)[1]
                    else:
                        skill_list_str = skill_category_str
                        
                    for part in re.split(r"[,;/]", skill_list_str):
                        token = part.strip().lower()
                        if len(token) > 2:
                            keywords.add(token)
                            
            # Extract from core achievements text
            for achieve in matrix_data.get("core_achievements", []):
                # Clean out company [Tags] for naive keyword match
                clean_target = re.sub(r'\[.*?\]', '', achieve)
                for part in re.split(r"[\s,;.-]", clean_target):
                    token = re.sub(r'[^a-z]', '', part.lower())
                    if 3 <= len(token) <= 30:
                        keywords.add(token)
                        
        except Exception as e:
            logging.warning(f"Error extracting keywords from sparse matrix: {e}")
            
        return keywords

    # ------------------------- Role Judge & ATS ------------------------- #

    def _load_tpm_overlay(self) -> Dict[str, Any]:
        if self._tpm_overlay is not None:
            return self._tpm_overlay
        if os.path.exists(TPM_OVERLAY_PATH):
            try:
                with open(TPM_OVERLAY_PATH, "r") as f:
                    self._tpm_overlay = yaml.safe_load(f) or {}
            except Exception:
                self._tpm_overlay = {}
        else:
            self._tpm_overlay = {}
        ov = self._tpm_overlay
        return ov if isinstance(ov, dict) else {}

    def _load_content_pillars_md(self) -> str:
        if self._content_pillars_md is not None:
            return self._content_pillars_md
        path = os.path.join(
            RESUME_AGENT_BASE_DIR,
            "skills",
            "resume_generation",
            "rules",
            "content_judgment_pillars.md",
        )
        try:
            with open(path, "r") as f:
                self._content_pillars_md = f.read()
        except Exception:
            self._content_pillars_md = ""
        return self._content_pillars_md

    def _load_judge_workflow_md(self) -> str:
        if self._judge_workflow_md is not None:
            return self._judge_workflow_md
        path = os.path.join(
            RESUME_AGENT_BASE_DIR,
            "workflows",
            "judge_content.md",
        )
        try:
            with open(path, "r") as f:
                self._judge_workflow_md = f.read()
        except Exception:
            self._judge_workflow_md = ""
        return self._judge_workflow_md

    def _is_tpm_product_role(self, title: str, recommended_resume: str) -> bool:
        """Heuristic routing: decide if this job belongs to the TPM/Product cluster."""
        title_l = (title or "").lower()
        rec_l = (recommended_resume or "").lower()

        # Title-based hints
        title_hits = any(
            kw in title_l
            for kw in [
                "product manager",
                "product management",
                "technical program manager",
                "tpm",
                "product owner",
                "product operations",
                "product ops",
                "program manager",
            ]
        )

        # Recommended-resume-based hints
        rec_hits = any(
            kw in rec_l
            for kw in [
                "tpm",
                "product",
                "product manager",
                "product owner",
                "product ops",
            ]
        )
        return bool(title_hits or rec_hits)

    def _compute_ats_coverage(
        self,
        jd_text: str,
        resume_text: str,
        overlay: Dict[str, Any],
    ) -> Tuple[int, str, Dict[str, Any]]:
        """
        Lightweight ATS-style check:
        - use overlay priority_keywords / critical_keywords
        - compute presence in resume_text
        - return (match_pct, critical_missing_csv, debug_stats)
        """
        jd_lower = (jd_text or "").lower()
        res_lower = (resume_text or "").lower()

        priority = [k.strip().lower() for k in overlay.get("priority_keywords", []) if k]
        critical = [k.strip().lower() for k in overlay.get("critical_keywords", []) if k]

        present = 0
        for kw in priority:
            if kw and kw in res_lower:
                present += 1
        total = len(priority) or 1
        match_pct = int(round(100 * present / total))

        critical_missing = [kw for kw in critical if kw and kw not in res_lower and kw in jd_lower]
        critical_missing_csv = ", ".join(sorted(set(critical_missing)))

        debug = {
            "priority_total": len(priority),
            "priority_present": present,
            "critical_missing": critical_missing,
        }
        return match_pct, critical_missing_csv, debug

    def _load_default_role_yaml_text(self) -> str:
        """Load the default TPM/Product role YAML as plain text if available."""
        try:
            if os.path.exists(DEFAULT_ROLE_YAML_PATH):
                with open(DEFAULT_ROLE_YAML_PATH, "r") as f:
                    return f.read()
        except Exception:
            pass
        return ""

    def _run_role_judge_and_ats(
        self,
        job: Dict[str, Any],
        jd_text: str,
        final_score: int,
        recommended_resume: str,
    ) -> Dict[str, Any]:
        """
        Run a role-aware judge + ATS-style check for TPM/Product jobs.
        Returns a dict with optional role_judge_* and ats_* fields.
        """
        # Route only high-conviction TPM/Product jobs
        if final_score < 70:
            return {}
        title = job.get("Role Title") or ""
        if not self._is_tpm_product_role(title, recommended_resume):
            return {}

        overlay = self._load_tpm_overlay()
        pillars_md = self._load_content_pillars_md()
        workflow_md = self._load_judge_workflow_md()
        resume_yaml_text = self._load_default_role_yaml_text()

        if not overlay or not resume_yaml_text:
            return {}

        ats_match_pct, ats_critical_csv, ats_debug = self._compute_ats_coverage(
            jd_text, resume_yaml_text, overlay
        )

        # Single LLM call that sees rubric, overlay, JD, resume, and ATS stats.
        system_prompt = (
            "You are a senior hiring-bar resume judge for Product Manager / TPM roles.\n"
            "You must:\n"
            "- Evaluate the resume content against the hiring bar using the provided pillars.\n"
            "- Consider the target job description and overlay role expectations.\n"
            "- Use the static ATS stats as hints, but do not fabricate experience.\n"
            "- Return ONLY a JSON object with the specified schema.\n\n"
            "CONTENT_JUDGMENT_PILLARS_MD:\n"
            f"{pillars_md}\n\n"
            "CONTENT_JUDGE_WORKFLOW_MD:\n"
            f"{workflow_md}\n"
        )

        user_prompt = (
            "### TARGET JOB DESCRIPTION\n"
            f"{jd_text}\n\n"
            "### RESUME ROLE YAML (SOURCE OF TRUTH)\n"
            f"{resume_yaml_text}\n\n"
            "### ROLE OVERLAY (TPM/Product)\n"
            f"{json.dumps(overlay, ensure_ascii=False, indent=2)}\n\n"
            "### STATIC ATS STATS\n"
            f"match_pct: {ats_match_pct}\n"
            f"critical_missing: {ats_critical_csv or 'None'}\n"
            f"debug: {json.dumps(ats_debug, ensure_ascii=False)}\n\n"
            "INSTRUCTIONS:\n"
            "Return ONLY a JSON object with this schema:\n"
            "{\n"
            '  \"role_judge_score\": int,              // 0-100\n'
            '  \"role_judge_verdict\": str,            // e.g., \"Ready\", \"Needs more scope\"\n'
            '  \"role_judge_notes\": str,              // 1-2 line human summary\n'
            '  \"pillar_ratings\": {                   // optional per-pillar scores 0-3\n'
            '      \"Strategic Experience Argument\": int,\n'
            '      \"Recruiter Empathy\": int,\n'
            '      \"Hard Skill Depth\": int,\n'
            '      \"Tool & Application Mastery\": int,\n'
            '      \"Methodological Rigor\": int,\n'
            '      \"Soft Skill Integration\": int,\n'
            '      \"Keyword Naturalism\": int,\n'
            '      \"AI-Forwardness\": int\n'
            "  },\n"
            '  \"improvement_suggestions\": [str],     // up to 3 concise bullet suggestions\n'
            '  \"ats_match_pct\": int,                 // echo/refine static match % (0-100)\n'
            '  \"ats_critical_gaps\": [str],           // list of critical missing terms\n'
            '  \"ats_notes\": str                      // 1 short sentence about ATS alignment\n'
            "}\n"
            "Do not include markdown code fences, commentary, or any extra text."
        )

        eval_cfg = get_evaluation_config()
        eval_model = eval_cfg.get("gemini_model")
        raw, engine_used = self.llm.generate_content(
            system_prompt,
            user_prompt,
            formatting_instruction=self.formatting_instruction,
            model=eval_model,
        )
        if engine_used == "FAILED" or not raw:
            return {
                "role_judge_score": "",
                "role_judge_verdict": "",
                "role_judge_notes": "Judge failed (LLM error).",
                "ats_match_pct": ats_match_pct,
                "ats_critical_gaps": ats_critical_csv,
            }

        try:
            text = raw.strip()
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise ValueError("No JSON object found in role judge output.")
            obj = json.loads(text[start : end + 1])
        except Exception as e:
            logging.warning(f"Role judge JSON parse failed: {e}")
            return {
                "role_judge_score": "",
                "role_judge_verdict": "",
                "role_judge_notes": "Judge failed (parse error).",
                "ats_match_pct": ats_match_pct,
                "ats_critical_gaps": ats_critical_csv,
            }

        # Heal and normalize fields
        def _to_int_safe(v: Any, default: int = 0) -> int:
            try:
                if v is None or v == "":
                    return default
                if isinstance(v, bool):
                    return default
                return int(str(v).strip())
            except Exception:
                return default

        role_judge_score = _to_int_safe(obj.get("role_judge_score"), default=0)
        role_judge_score = max(0, min(100, role_judge_score))
        ats_pct_out = _to_int_safe(obj.get("ats_match_pct"), default=ats_match_pct)
        ats_pct_out = max(0, min(100, ats_pct_out))

        ats_crit = obj.get("ats_critical_gaps") or []
        if isinstance(ats_crit, str):
            ats_crit_list = [s.strip() for s in ats_crit.split(",") if s.strip()]
        elif isinstance(ats_crit, list):
            ats_crit_list = [str(s).strip() for s in ats_crit if str(s).strip()]
        else:
            ats_crit_list = []

        return {
            "role_judge_score": role_judge_score,
            "role_judge_verdict": str(obj.get("role_judge_verdict") or "").strip(),
            "role_judge_notes": str(obj.get("role_judge_notes") or "").strip(),
            "ats_match_pct": ats_pct_out,
            "ats_critical_gaps": ", ".join(sorted(set(ats_crit_list))) or ats_critical_csv,
        }

    def count_skill_overlap(self, jd_text, keywords=None):
        """Count how many profile skill keywords appear in the JD. Used to nudge away from Maybe when >= 5."""
        keywords = keywords or self.get_profile_skill_keywords()
        if not keywords:
            return 0
        jd_lower = (jd_text or "").lower()
        return sum(1 for kw in keywords if kw in jd_lower)

    @staticmethod
    def _extract_top_level_json_object_strings(text: str) -> List[str]:
        """Successive top-level `{...}` objects (handles one blob with multiple evals)."""
        out: List[str] = []
        decoder = json.JSONDecoder()
        n = len(text)
        i = 0
        while i < n:
            j = text.find("{", i)
            if j == -1:
                break
            try:
                _, end = decoder.raw_decode(text[j:])
                out.append(text[j : j + end])
                i = j + end
            except json.JSONDecodeError:
                i = j + 1
        return out

    def _split_batch_evaluation_blocks(self, raw_text: str, expected: int) -> List[str]:
        """
        One string per job: split on ---EVAL---, else parse multiple JSON objects from one blob.
        """
        raw_text = (raw_text or "").strip()
        if expected <= 0:
            return []
        parts = [
            p.strip()
            for p in re.split(r"\s*---\s*EVAL\s*---\s*", raw_text, flags=re.IGNORECASE)
            if p.strip()
        ]
        if len(parts) >= expected:
            return parts[:expected]
        candidates = self._extract_top_level_json_object_strings(raw_text)
        if len(candidates) >= expected:
            return candidates[:expected]
        if parts:
            return parts + [""] * (expected - len(parts))
        if candidates:
            return candidates + [""] * (expected - len(candidates))
        return [""] * expected

    def parse_evaluation(self, raw_text):
        """
        Parses LLM output into a structured evaluation tuple.
        Prioritizes JSON parsing, falls back to Regex if needed.
        """
        text = raw_text.strip()
        
        # JSON-only: if we can't parse strict schema, we treat it as NEEDS_REVIEW upstream.
        # Find the first { and last } to handle potential conversational noise.
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found in model output.")
        json_str = text[start : end + 1]
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as first_err:
            repaired = _repair_reasoning_json_newlines(json_str)
            try:
                data = json.loads(repaired)
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON parse error after repair: {e}") from first_err

        # HEAL JSON: Handle common LLM quirks (like returning lists for scalar fields)
        score = data.get("apply_conviction_score", 0)
        if isinstance(score, list) and score:
            score = score[0]
        try:
            score_str = str(score).strip("[]* ")
            score = int(score_str) if score_str else 0
        except Exception:
            score = 0
        data["apply_conviction_score"] = max(0, min(100, int(score)))

        for field in ["verdict", "recommended_resume", "h1b_sponsorship", "location_verification", "jd_quality", "output_quality"]:
            if field in data:
                data[field] = str(data[field]).strip("[]* ")

        for field in ["tech_stack", "skill_gaps"]:
            if field in data and isinstance(data[field], str):
                data[field] = [s.strip() for s in data[field].split(",") if s.strip()]

        validated = JobEvaluationSchema(**data)

        breakdown = validated.score_breakdown or {}
        if breakdown:
            total = 0
            for v in breakdown.values():
                if isinstance(v, int):
                    total += v
                else:
                    # Any non-int component => low quality
                    data["output_quality"] = "low"
                    validated = JobEvaluationSchema(**data)
                    break
            if total != int(validated.apply_conviction_score):
                data["output_quality"] = "low"
                data["confidence"] = float(min(0.5, float(data.get("confidence", 0.5) or 0.5)))
                validated = JobEvaluationSchema(**data)

        return (
            validated.verdict,
            validated.recommended_resume,
            validated.h1b_sponsorship,
            validated.location_verification,
            ", ".join(validated.skill_gaps),
            validated.reasoning,
            validated.salary_range,
            ", ".join(validated.tech_stack),
            validated.apply_conviction_score,
        )

    def _compute_fallback_score(self, jd_text: str, location: str) -> int:
        """
        Compute Apply Conviction Score when LLM returns no score (parse failure or missing).
        Used by evaluate_all and testable without sheets/LLM.
        """
        keywords = self.get_profile_skill_keywords()
        overlap = self.count_skill_overlap(jd_text or "", keywords)
        score = min(50, overlap * 10)
        priority = self.get_strategic_priority(location)
        if "HIGH" in priority:
            score += 20
        if "MEDIUM" in priority:
            score += 10
        return score

    def _retry_single_job_eval_raw(
        self,
        job: Any,
        grounded_sys_prompt: str,
        profile_keywords: Any,
        eval_model: Optional[str],
        jd_cap: int,
    ) -> Tuple[str, str]:
        """Second LLM call with one job only when batch output was missing/invalid for that row."""
        job_link = job.get("Job Link") or job.get("url") or ""
        jd_text = (self.sheets_client.get_jd_for_url(job_link) or "").strip()
        if not jd_text:
            return "", "FAILED"
        company = job.get("Company") or ""
        location = job.get("Location") or ""
        jd_prompt = _clip_jd_for_batch_prompt(jd_text, jd_cap) if jd_cap > 0 else jd_text
        sponsor_info = self.get_verified_sponsorship(company)
        priority = self.get_strategic_priority(location)
        overlap = self.count_skill_overlap(jd_text, profile_keywords)
        nudge = f"\n[Pre-check: {overlap} skill overlap.]"
        user_prompt = (
            f"### JOB POSTING\n"
            f"Title: {job.get('Role Title')}\n"
            f"Company: {company}\n"
            f"Strategic Priority: {priority}\n"
            f"Verified Sponsorship History: {sponsor_info}\n"
            f"JD Content: {jd_prompt}{nudge}"
        )
        return self.llm.generate_content(
            grounded_sys_prompt,
            user_prompt,
            formatting_instruction=self.formatting_instruction,
            model=eval_model,
        )

    def evaluate_all(self, mode="NEW", limit=None, cycle_id: Optional[str] = None):
        eval_cfg = get_evaluation_config()
        learn_cfg = get_learning_config()
        if limit is None:
            limit = eval_cfg.get("limit", 300)
        sheet_batch_size = eval_cfg.get("sheet_batch_size", SHEET_BATCH_SIZE_DEFAULT)
        batch_size = eval_cfg.get("batch_eval_size", BATCH_EVAL_SIZE_DEFAULT)
        jd_cap_batch = int(eval_cfg.get("batch_jd_max_chars", 0) or 0)
        skip_llm_below = int(eval_cfg.get("skip_llm_if_fallback_below", 0) or 0)
        snippet_first_enabled = bool(eval_cfg.get("snippet_first_enabled", False))
        snippet_first_chars = int(eval_cfg.get("snippet_first_chars", 2200) or 2200)
        gray_zone_retry = bool(eval_cfg.get("gray_zone_full_jd_retry", True))
        gray_min = int(eval_cfg.get("gray_zone_min_score", 68) or 68)
        gray_max = int(eval_cfg.get("gray_zone_max_score", 82) or 82)
        if gray_max < gray_min:
            gray_min, gray_max = gray_max, gray_min
        eval_model = eval_cfg.get("gemini_model")
        tailor_min = int(eval_cfg.get("tailor_min_score", 90))

        cid = cycle_id or os.environ.get("PIPELINE_CYCLE_ID", "")

        print(f"Evaluation backend: {self.llm.provider}")

        if mode == "MAYBE":
            print("Fetching 'Maybe' jobs for re-evaluation...")
            new_jobs, worksheet = self.sheets_client.get_maybe_jobs(limit=limit)
        elif mode == "NEEDS_REVIEW":
            print("Fetching NEEDS_REVIEW jobs for re-evaluation...")
            new_jobs, worksheet = self.sheets_client.get_needs_review_jobs(limit=limit)
        elif mode == "LLM_FAILED":
            print("Fetching LLM_FAILED jobs for re-evaluation...")
            new_jobs, worksheet = self.sheets_client.get_llm_failed_jobs(limit=limit)
        else:
            print("Fetching NEW jobs from Google Sheets...")
            new_jobs, worksheet = self.sheets_client.get_new_jobs(limit=limit)
        
        if not new_jobs:
            print(f"No {mode} jobs to evaluate!")
            return []

        print(f"Found {len(new_jobs)} jobs. Loading Context...")
        sys_prompt = self.load_system_prompt()
        profiles_prompt = self.load_user_profiles()
        story_excerpt = self.load_interview_story_bank_excerpt()

        already_seen = self.sheets_client.get_already_evaluated_or_applied_canonical_urls()
        grounded_sys_prompt = (
            f"{sys_prompt}\n\n### USER PROFILE SUMMARY\n{profiles_prompt}{story_excerpt}"
        )
        
        profile_keywords = self.get_profile_skill_keywords()
        evaluated_match_types = []
        high_scoring_tailor_jobs = []

        # Track updates per worksheet to minimize API calls
        updates_by_ws: Any = {}

        # --- 0. DUPLICATE / ALREADY-SEEN ---
        to_eval: Any = []
        for job in new_jobs: # type: ignore
            canonical = normalize_job_url(job.get("Job Link") or job.get("url") or "")
            target_ws = job.get("_worksheet") or worksheet
            
            # Re-eval modes: URL may already be EVALUATED elsewhere; still re-run these rows.
            is_reeval_mode = mode in ("MAYBE", "NEEDS_REVIEW", "LLM_FAILED")

            if canonical and canonical in already_seen and not is_reeval_mode:
                print(f"  Skip (already seen): {job.get('Role Title')} at {job.get('Company')}")
                if target_ws not in updates_by_ws: updates_by_ws[target_ws] = []
                updates_by_ws[target_ws].append(
                    build_evaluation_update(
                        job["_row_index"],
                        "Already seen",
                        "—",
                        "N/A",
                        "N/A",
                        "Duplicate; skipped.",
                        0,
                        "Duplicate; skipped.",
                    )
                )
                evaluated_match_types.append("Already seen")
                continue
            to_eval.append(job)

        # --- 1. FAST FILTER ---
        new_to_eval = []
        for job in to_eval:
            if mode == "NEW":
                passed, reject_reason = self.passes_initial_filter(job)
                if not passed:
                    print(f"  Filtered: {job.get('Role Title')} -> {reject_reason}")
                    target_ws = job.get("_worksheet") or worksheet
                    if target_ws not in updates_by_ws: updates_by_ws[target_ws] = []
                    updates_by_ws[target_ws].append(
                        build_evaluation_update(
                            job["_row_index"],
                            "❌ No",
                            "None (Filtered)",
                            "N/A",
                            "N/A",
                            reject_reason,
                            0,
                            reject_reason,
                        )
                    )
                    evaluated_match_types.append("❌ No")
                    continue
            new_to_eval.append(job)
        to_eval = new_to_eval

        # --- 2. BATCH LLM EVALUATION ---
        for chunk_start in range(0, len(to_eval), batch_size):
            chunk = to_eval[chunk_start : chunk_start + batch_size] # type: ignore
            chunk_eval: List[Any] = []
            job_contexts: List[str] = []
            snippet_used_rows: set[int] = set()
            for job in chunk:
                job_link = job.get("Job Link") or job.get("url") or ""
                company = job.get("Company") or ""
                location = job.get("Location") or ""
                jd_text = (self.sheets_client.get_jd_for_url(job_link) or "").strip()
                
                # FALLBACK: If there is no real JD text, flag it immediately and do not evaluate.
                if not jd_text or jd_text.lower() == "none":
                    target_ws = job.get("_worksheet") or worksheet
                    if target_ws not in updates_by_ws: updates_by_ws[target_ws] = []
                    updates_by_ws[target_ws].append(
                        build_evaluation_update(
                            job["_row_index"],
                            "⚠️ Missing JD",
                            "Unknown",
                            "N/A",
                            "N/A",
                            "JD could not be scraped; skipped evaluation.",
                            0,
                            "Missing JD",
                        )
                    )  # type: ignore
                    evaluated_match_types.append("⚠️ Missing JD")
                    continue

                # Optional token saver: skip LLM calls for rows that a deterministic heuristic
                # already estimates below threshold.
                if skip_llm_below > 0:
                    est_score = self._compute_fallback_score(jd_text, location)
                    if est_score < skip_llm_below:
                        target_ws = job.get("_worksheet") or worksheet
                        if target_ws not in updates_by_ws:
                            updates_by_ws[target_ws] = []
                        reason = (
                            f"Skipped LLM by pre-gate: fallback estimate {est_score} < "
                            f"{skip_llm_below}."
                        )
                        updates_by_ws[target_ws].append(
                            build_evaluation_update(
                                job["_row_index"],
                                "📉 Low Priority",
                                "None (Pre-gate)",
                                "N/A",
                                "N/A",
                                reason,
                                est_score,
                                reason,
                            )
                        )  # type: ignore
                        evaluated_match_types.append("📉 Low Priority")
                        continue
                
                chunk_eval.append(job)
                sponsor_info = self.get_verified_sponsorship(company)
                priority = self.get_strategic_priority(location)
                
                overlap = self.count_skill_overlap(jd_text, profile_keywords)
                nudge = f"\n[Pre-check: {overlap} skill overlap.]"
                jd_for_prompt = _clip_jd_for_batch_prompt(jd_text, jd_cap_batch)
                if snippet_first_enabled and snippet_first_chars > 0 and len(jd_for_prompt) > snippet_first_chars:
                    jd_for_prompt = jd_for_prompt[:snippet_first_chars]
                    try:
                        snippet_used_rows.add(int(job.get("_row_index", 0)))
                    except Exception:
                        pass

                job_context = (
                    f"### JOB POSTING {len(job_contexts) + 1}\n"
                    f"Title: {job.get('Role Title')}\n"
                    f"Company: {company}\n"
                    f"Strategic Priority: {priority}\n"
                    f"Verified Sponsorship History: {sponsor_info}\n"
                    f"JD Content: {jd_for_prompt}{nudge}"
                )
                job_contexts.append(job_context)
            
            if not chunk_eval:
                continue

            user_prompt = "\n\n".join(job_contexts)
            if len(chunk_eval) > 1:
                user_prompt += (
                    f"\n\nEvaluate each job separately. Output exactly {len(chunk_eval)} JSON objects "
                    "in the same order as JOB POSTING 1..n. Between objects put a line with only: ---EVAL---"
                )

            print(f"  Batch evaluating jobs {chunk_start+1}-{chunk_start+len(chunk_eval)} ({len(chunk_eval)} with JD)...")
            raw_text, engine_used = self.llm.generate_content(
                grounded_sys_prompt, user_prompt, 
                formatting_instruction=self.formatting_instruction,
                model=eval_model
            )

            if engine_used == "FAILED":
                for job in chunk_eval:
                    target_ws = job.get("_worksheet") or worksheet
                    if target_ws not in updates_by_ws: updates_by_ws[target_ws] = []
                    fail_note = (
                        "LLM request failed (timeout, rate limit, or provider error). "
                        "No conviction score; re-run after checking API keys and quotas."
                    )
                    updates_by_ws[target_ws].append(
                        build_evaluation_update(
                            job["_row_index"],
                            "NEEDS_REVIEW",
                            "Unknown",
                            "N/A",
                            "N/A",
                            fail_note,
                            0,
                            fail_note,
                            evidence_json=json.dumps(
                                {"error": "llm_failed", "engine": str(engine_used)},
                                ensure_ascii=False,
                            ),
                        )
                    )  # type: ignore
                    evaluated_match_types.append("NEEDS_REVIEW")
                continue

            blocks = self._split_batch_evaluation_blocks(raw_text, len(chunk_eval))
            for job, block in zip(chunk_eval, blocks):
                target_ws = job.get("_worksheet") or worksheet
                if target_ws not in updates_by_ws: updates_by_ws[target_ws] = []

                block_text = (block or "").strip()
                if not block_text:
                    print(f"    ↻ Empty batch slot → single-job retry: {job.get('Role Title')}")
                    r_raw, r_eng = self._retry_single_job_eval_raw(
                        job, grounded_sys_prompt, profile_keywords, eval_model, jd_cap_batch
                    )
                    if r_eng != "FAILED":
                        block_text = (r_raw or "").strip()

                parsed: Optional[Tuple[Any, ...]] = None
                parse_err: Optional[BaseException] = None
                if block_text:
                    try:
                        parsed = self.parse_evaluation(block_text)
                    except Exception as e:
                        parse_err = e

                if parsed is None and block_text:
                    print(f"    ↻ Parse error → single-job retry: {job.get('Role Title')}")
                    r_raw, r_eng = self._retry_single_job_eval_raw(
                        job, grounded_sys_prompt, profile_keywords, eval_model, jd_cap_batch
                    )
                    if r_eng != "FAILED" and (r_raw or "").strip():
                        block_text = (r_raw or "").strip()
                        try:
                            parsed = self.parse_evaluation(block_text)
                            parse_err = None
                        except Exception as e2:
                            parse_err = e2

                if parsed is None:
                    fallback = "NEEDS_REVIEW"
                    if parse_err:
                        updates_by_ws[target_ws].append(
                            build_evaluation_update(
                                job["_row_index"],
                                fallback,
                                "Unknown",
                                "N/A",
                                "N/A",
                                "Model output invalid. Needs review.",
                                0,
                                "Model output invalid. Needs review.",
                                evidence_json=json.dumps(
                                    {
                                        "error": "parse_error",
                                        "message": str(parse_err),
                                        "raw": (block_text or "")[:4000],
                                    },
                                    ensure_ascii=False,
                                ),
                            )
                        )
                    else:
                        updates_by_ws[target_ws].append(
                            build_evaluation_update(
                                job["_row_index"],
                                fallback,
                                "Unknown",
                                "N/A",
                                "N/A",
                                "Model output missing/invalid. Needs review.",
                                0,
                                "Model output missing/invalid. Needs review.",
                                evidence_json=json.dumps(
                                    {
                                        "error": "empty_block_or_split_failure",
                                        "raw": (block_text or "")[:1000],
                                    },
                                    ensure_ascii=False,
                                ),
                            )
                        )
                    evaluated_match_types.append(fallback)
                    continue

                match_type, rec, h1b, loc, missing, reasoning, salary, tech, score = parsed
                try:
                    row_ix = int(job.get("_row_index", 0))
                except Exception:
                    row_ix = 0
                if (
                    gray_zone_retry
                    and row_ix in snippet_used_rows
                    and gray_min <= int(score) <= gray_max
                ):
                    print(
                        f"    ↻ Gray-zone ({score}) from snippet pass → full-JD retry: "
                        f"{job.get('Role Title')}"
                    )
                    r_raw2, r_eng2 = self._retry_single_job_eval_raw(
                        job, grounded_sys_prompt, profile_keywords, eval_model, 0
                    )
                    if r_eng2 != "FAILED" and (r_raw2 or "").strip():
                        try:
                            parsed2 = self.parse_evaluation((r_raw2 or "").strip())
                            (
                                match_type,
                                rec,
                                h1b,
                                loc,
                                missing,
                                reasoning,
                                salary,
                                tech,
                                score,
                            ) = parsed2
                            block_text = (r_raw2 or "").strip()
                        except Exception:
                            pass

                evidence_json = ""
                try:
                    start = block_text.find("{")
                    end = block_text.rfind("}")
                    if start != -1 and end != -1:
                        obj = json.loads(block_text[start : end + 1])
                        evidence_json = json.dumps(
                            {
                                "score_breakdown": obj.get("score_breakdown") or {},
                                "evidence": obj.get("evidence") or [],
                                "confidence": obj.get("confidence"),
                                "jd_quality": obj.get("jd_quality"),
                                "output_quality": obj.get("output_quality"),
                            },
                            ensure_ascii=False,
                        )
                except Exception:
                    evidence_json = ""

                jd_link = job.get("Job Link") or job.get("url") or ""
                jd_text = (self.sheets_client.get_jd_for_url(jd_link) or "").strip()

                # FALLBACK CALCULATION: If LLM failed score or was 0, use metrics
                if score == 0:
                    current_jd = self.sheets_client.get_jd_for_url(jd_link) or ""
                    score = self._compute_fallback_score(current_jd, job.get("Location") or "")

                base_score = score

                # Post-LLM calibration (learned patterns)
                if learn_cfg.get("enabled", True):
                    max_delta = int(learn_cfg.get("max_abs_delta", 15))
                    pp = learn_cfg.get("patterns_path", "data/learned_patterns.yaml")
                    ppath = pp if os.path.isabs(pp) else os.path.join(os.getcwd(), pp)
                    patterns = _load_patterns(ppath)
                    final_score, audit = apply_calibration(
                        base_score,
                        jd_text,
                        title=job.get("Role Title") or "",
                        company=job.get("Company") or "",
                        patterns=patterns,
                        max_abs_delta=max_delta,
                        cycle_id=cid,
                    )
                else:
                    final_score = base_score
                    audit = DecisionAudit(
                        base_llm_score=base_score,
                        calibration_delta=0,
                        final_score=base_score,
                        matched_patterns=[],
                        cycle_id=cid,
                    )

                # Tiered Verdict Mapping (single source of truth)
                match_type = score_to_verdict(final_score)

                if final_score >= tailor_min:
                    job_payload = job.copy()
                    job_payload["evaluation_score"] = final_score
                    job_payload["description"] = jd_text
                    job_payload["recommended_resume"] = rec
                    high_scoring_tailor_jobs.append(job_payload)

                # Update all caches
                eval_results = {
                    "h1b": h1b,
                    "missing_skills": missing,
                    "salary": salary,
                    "tech_stack": tech,
                    "recommended_resume": rec,
                    "score": final_score,
                }
                self.update_sponsorship_cache(job.get("Company"), h1b)
                self.update_intelligence_caches(job, eval_results)

                # Optional role-aware judge + ATS enrichment (TPM/Product cluster only)
                judge_fields: Dict[str, Any] = self._run_role_judge_and_ats(
                    job=job,
                    jd_text=jd_text,
                    final_score=final_score,
                    recommended_resume=rec,
                )

                # Prefer dict update path so we can attach extra columns without
                # breaking legacy tuple callers.
                update_payload: Dict[str, Any] = {
                    "row_index": job["_row_index"],
                    "match_type": match_type,
                    "recommended": rec,
                    "h1b": h1b,
                    "loc_ver": loc,
                    "missing": missing,
                    "score": final_score,
                    "reasoning": reasoning,
                    "calibration_delta": audit.calibration_delta,
                    "decision_audit_json": audit.to_json(),
                    "base_llm_score": base_score,
                    "evidence_json": evidence_json,
                }
                update_payload.update(judge_fields)

                deep_path = self._run_deep_job_packet(
                    job=job,
                    jd_text=jd_text,
                    final_score=final_score,
                    reasoning=reasoning,
                    recommended_resume=rec,
                    h1b=h1b,
                    evidence_json=evidence_json,
                )
                update_payload["deep_packet"] = deep_path or ""
                if deep_path and not deep_path.startswith("ERROR"):
                    print(f"    📄 Deep packet: {deep_path}")

                tailor_path = self._write_tailor_payload_json(
                    job=job,
                    jd_text=jd_text,
                    final_score=final_score,
                    recommended_resume=rec,
                    missing=missing,
                    evidence_json=evidence_json,
                )
                updates_by_ws[target_ws].append(update_payload)  # type: ignore
                evaluated_match_types.append(match_type)
                print(f"    ✅ Eval complete: {job.get('Role Title')} -> {match_type} ({final_score})")

            # --- PERIODIC SYNC (Every 2 jobs to show immediate progress) ---
            for ws, batch in updates_by_ws.items():
                if len(batch) >= 2:
                    print(f"\n  -> Periodic Sync: Updating {len(batch)} jobs in '{ws.title}'...") # type: ignore
                    self.sheets_client.update_evaluated_jobs(ws, batch)
                    batch.clear() 

        # 3. Final Batch Save
        if updates_by_ws:
            print("\nSaving all evaluations to Google Sheets...")
            for ws, batch in updates_by_ws.items():
                if batch:
                    print(f"  Updating {len(batch)} jobs in '{ws.title}'...") # type: ignore
                    self.sheets_client.update_evaluated_jobs(ws, batch)

        # 4. Save and Summarize
        self.save_all_caches()

        high_priority_count = 0
        if evaluated_match_types:
            dist = Counter(evaluated_match_types)
            high_priority_count = dist.get("🚀 Must-Apply", 0) + dist.get("✅ Strong Match", 0)
            
            total = len(evaluated_match_types)
            print("\n--- Match Type distribution ---")
            labels = [
                "🚀 Must-Apply",
                "✅ Strong Match",
                "⚡ Ambitious Match",
                "⚖️ Worth Considering",
                "📉 Low Priority",
                "❌ No",
                "Already seen",
            ]
            for label in labels:
                n = dist.get(label, 0)
                pct = (100 * n / total) if total else 0
                print(f"  {label}: {n} ({pct:.0f}%)")
            
            # Check for overly cautious scoring (legacy "Maybe" warning updated for "No" or low scores)
            no_pct = (100 * dist.get("❌ No", 0) / total) if total else 0
            if no_pct > 80:
                print("\n  ⚠ Calibration warning: >80% of jobs are 'No'. Consider audit of sourcing queries or JD pre-parsing.")

        print("\nDone! Sorting the Google Sheet by match priority...")
        self.sheets_client.sort_daily_jobs()
        return high_scoring_tailor_jobs

    def save_batch_if_needed(self, updates_list, worksheet, batch_size=25):
        """Helper to save in batches to avoid losing progress and reduce API calls."""
        if len(updates_list) >= batch_size:
            print(f"  -> Saving batch of {batch_size} to Google Sheets...")
            self.sheets_client.update_evaluated_jobs(worksheet, updates_list)
            updates_list.clear() # clear list in place

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Evaluate jobs from Google Sheets (legacy evaluator).")
    ap.add_argument(
        "--mode",
        default="NEW",
        choices=["NEW", "MAYBE", "NEEDS_REVIEW", "LLM_FAILED"],
        help="NEW = Status NEW; MAYBE = re-eval Maybe rows; NEEDS_REVIEW = re-eval failed-parse rows on today's tab; LLM_FAILED = re-eval rows with LLM failure text/zero-score signals.",
    )
    ap.add_argument("--limit", type=int, default=None, help="Max rows to fetch (default: config evaluation limit).")
    args = ap.parse_args()
    evaluator = JobEvaluator()
    evaluator.evaluate_all(mode=args.mode, limit=args.limit)
