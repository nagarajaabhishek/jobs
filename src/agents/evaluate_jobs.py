import logging
import os
import re
import yaml
import json
from collections import Counter

from src.core.google_sheets_client import GoogleSheetsClient, normalize_job_url
from src.core.llm_router import LLMRouter
from src.core.config import get_evaluation_config
from src.core.job_filters import passes_evaluation_prefilter
from src.core.schemas import JobEvaluationSchema

# Fallback when config not used
BATCH_EVAL_SIZE_DEFAULT = 4
SHEET_BATCH_SIZE_DEFAULT = 25


def score_to_verdict(score: int) -> str:
    """Map Apply Conviction Score to tiered verdict. Single source of truth for tests and evaluate_all."""
    if score >= 85:
        return "🔥 Auto-Apply"
    if score >= 70:
        return "✅ Strong Match"
    if score >= 50:
        return "⚖️ Worth Considering"
    return "❌ No"


class JobEvaluator:
    def __init__(self):
        self.sheets_client = GoogleSheetsClient()
        self.llm = LLMRouter()
        self.prompt_path = "src/prompts/gemini_job_fit_analyst.md"
        self.roles = sorted([
            "Product Manager (TPM)", "Product Owner (PO)", "Business Analyst (BA)", 
            "Scrum Master (SM)", "Manager", "Go-To Market (GTM)"
        ])
        
        # Load verified sponsors
        self.sponsors = {}
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

        self.formatting_instruction = (
            "\n\nCRITICAL INSTRUCTION: You MUST output ONLY a valid JSON object matching the exact "
            "schema provided in the base prompt. DO NOT include any conversational text, explanations, "
            "or markdown formatting blocks (like ```json)."
        )

    def get_verified_sponsorship(self, company):
        """Checks if a company has a verified sponsorship history."""
        if not company: return "Unknown"
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
        if not company or not status: return
        clean_company = company.strip()
        clean_status = status.strip()
        
        # We only cache definitive "Likely" or "Unlikely" status from the LLM
        # if the company isn't already verified with a strong record.
        if "Likely:" in clean_status or "Unlikely:" in clean_status:
            # Check if we already have it
            existing = self.sponsors.get(clean_company)
            if not existing or "LLM estimated" in existing or "Not in verified database" in str(existing):
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
        matrix_path = os.path.join(os.getcwd(), "data", "dense_master_matrix.json")
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
            print(f"  ⚠ Warning: Could not load dense matrix. Have you run build_dense_matrix.py? Error: {e}")
            return "Error: Dense matrix missing."

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

    def count_skill_overlap(self, jd_text, keywords=None):
        """Count how many profile skill keywords appear in the JD. Used to nudge away from Maybe when >= 5."""
        keywords = keywords or self.get_profile_skill_keywords()
        if not keywords:
            return 0
        jd_lower = (jd_text or "").lower()
        return sum(1 for kw in keywords if kw in jd_lower)



    def parse_evaluation(self, raw_text):
        """
        Parses LLM output into a structured evaluation tuple.
        Prioritizes JSON parsing, falls back to Regex if needed.
        """
        text = raw_text.strip()
        
        # 1. Try JSON Parsing first
        try:
            # Find the first { and last } to handle potential conversational noise
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                json_str = text[start:end+1]
                data = json.loads(json_str)
                
                # HEAL JSON: Handle common LLM quirks (like returning lists for scalar fields)
                # Conviction Score
                score = data.get("apply_conviction_score", 0)
                if isinstance(score, list) and score: score = score[0]
                try: 
                    score_str = str(score).strip("[]* ")
                    score = int(score_str) if score_str else 0
                except: score = 0
                data["apply_conviction_score"] = score
                
                # Clean up other fields
                for field in ["verdict", "recommended_resume", "h1b_sponsorship", "location_verification"]:
                    if field in data:
                        data[field] = str(data[field]).strip("[]* ")
                
                # Tech stack & Skill gaps (ensure lists)
                for field in ["tech_stack", "skill_gaps"]:
                    if field in data and isinstance(data[field], str):
                        data[field] = [s.strip() for s in data[field].split(",")]
                
                # Validate with Pydantic
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
                    validated.apply_conviction_score
                )
        except Exception as e:
            logging.debug(f"JSON Parsing failed, falling back to regex: {e}")

        # 2. REGEX FALLBACK (for corrupted JSON strings)
        def extract_str(key, default="Unknown"):
            # Matches "key": "value"
            pattern = rf'"{key}"\s*:\s*"([^"]+)"'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                val = match.group(1).strip("[]* \n\"")
                return val if val else default
            return default

        def extract_list(key, default="Unknown"):
            # Matches "key": ["val1", "val2"]
            pattern = rf'"{key}"\s*:\s*\[(.*?)\]'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                # Extract values from the array string
                inner = match.group(1)
                items = re.findall(r'"([^"]+)"', inner)
                return ", ".join(items) if items else default
            return default

        loc_ver = extract_str("location_verification")
        h1b_status = extract_str("h1b_sponsorship")
        recommended = extract_str("recommended_resume")
        reasoning = extract_str("reasoning")
        salary = extract_str("salary_range")
        match_type = extract_str("verdict")
        
        skills = extract_list("skill_gaps")
        tech_stack = extract_list("tech_stack")
        
        # Parse Score
        score_match = re.search(r'"apply_conviction_score"\s*:\s*(\d+)', text, re.IGNORECASE)
        score = int(score_match.group(1)) if score_match else 0
        score = max(0, min(100, score))

        return match_type, recommended, h1b_status, loc_ver, skills, reasoning, salary, tech_stack, score

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

    def evaluate_all(self, mode="NEW", limit=None):
        eval_cfg = get_evaluation_config()
        if limit is None:
            limit = eval_cfg.get("limit", 300)
        sheet_batch_size = eval_cfg.get("sheet_batch_size", SHEET_BATCH_SIZE_DEFAULT)
        batch_size = eval_cfg.get("batch_eval_size", BATCH_EVAL_SIZE_DEFAULT)

        print(f"Evaluation backend: {self.llm.provider}")

        if mode == "MAYBE":
            print("Fetching 'Maybe' jobs for re-evaluation...")
            new_jobs, worksheet = self.sheets_client.get_maybe_jobs(limit=limit)
        else:
            print("Fetching NEW jobs from Google Sheets...")
            new_jobs, worksheet = self.sheets_client.get_new_jobs(limit=limit)
        
        if not new_jobs:
            print(f"No {mode} jobs to evaluate!")
            return

        print(f"Found {len(new_jobs)} jobs. Loading Context...")
        sys_prompt = self.load_system_prompt()
        profiles_prompt = self.load_user_profiles()
        
        already_seen = self.sheets_client.get_already_evaluated_or_applied_canonical_urls()
        # Prepare role specializations text for Deep Match
        role_specs_text = "\n\n".join(self.role_summaries.values())
        grounded_sys_prompt = f"{sys_prompt}\n\n### USER PROFILE SUMMARY\n{profiles_prompt}\n\n### ROLE-SPECIFIC SPECIALIZATIONS (Use for Deep Matching)\n{role_specs_text}"
        
        profile_keywords = self.get_profile_skill_keywords()
        evaluated_match_types = []

        # Track updates per worksheet to minimize API calls
        updates_by_ws = {}

        # --- 0. DUPLICATE / ALREADY-SEEN ---
        to_eval = []
        for job in new_jobs:
            canonical = normalize_job_url(job.get("Job Link") or job.get("url") or "")
            target_ws = job.get("_worksheet") or worksheet
            
            # Calibration: In re-evaluation mode, we DON'T skip already seen if they are "Maybe"
            is_maybe_reeval = (mode == "MAYBE")
            
            if canonical and canonical in already_seen and not is_maybe_reeval:
                print(f"  Skip (already seen): {job.get('Role Title')} at {job.get('Company')}")
                if target_ws not in updates_by_ws: updates_by_ws[target_ws] = []
                updates_by_ws[target_ws].append((
                    job["_row_index"], "Already seen", "—", "N/A", "N/A", "Duplicate; skipped."
                ))
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
                    updates_by_ws[target_ws].append((
                        job["_row_index"], "Not at all", "None (Filtered)", "N/A", "N/A", reject_reason
                    ))
                    evaluated_match_types.append("Not at all")
                    continue
            new_to_eval.append(job)
        to_eval = new_to_eval

        # --- 2. BATCH LLM EVALUATION ---
        for chunk_start in range(0, len(to_eval), batch_size):
            chunk = to_eval[chunk_start : chunk_start + batch_size]
            job_contexts = []
            for i, job in enumerate(chunk):
                job_link = job.get("Job Link") or job.get("url") or ""
                company = job.get("Company") or ""
                location = job.get("Location") or ""
                jd_text = (self.sheets_client.get_jd_for_url(job_link) or "").strip()
                if not jd_text: jd_text = "[No JD in cache.]"
                
                # OPTIMIZATIONS: Verified Metadata
                sponsor_info = self.get_verified_sponsorship(company)
                priority = self.get_strategic_priority(location)
                
                overlap = self.count_skill_overlap(jd_text, profile_keywords)
                nudge = f"\n[Pre-check: {overlap} skill overlap.]"
                
                job_context = (
                    f"### JOB POSTING {i+1}\n"
                    f"Title: {job.get('Role Title')}\n"
                    f"Company: {company}\n"
                    f"Strategic Priority: {priority}\n"
                    f"Verified Sponsorship History: {sponsor_info}\n"
                    f"JD Content: {jd_text}{nudge}"
                )
                job_contexts.append(job_context)
            
            user_prompt = "\n\n".join(job_contexts)
            if len(chunk) > 1:
                user_prompt += "\n\nEvaluate each job separately. Separate with: ---EVAL---"

            print(f"  Batch evaluating {chunk_start+1}-{chunk_start+len(chunk)}...")
            eval_cfg = get_evaluation_config()
            eval_model = eval_cfg.get("gemini_model")
            
            raw_text, engine_used = self.llm.generate_content(
                grounded_sys_prompt, user_prompt, 
                formatting_instruction=self.formatting_instruction,
                model=eval_model
            )

            if engine_used == "FAILED":
                for job in chunk:
                    target_ws = job.get("_worksheet") or worksheet
                    if target_ws not in updates_by_ws: updates_by_ws[target_ws] = []
                    updates_by_ws[target_ws].append((job["_row_index"], "Maybe", "Unknown", "N/A", "N/A", "LLM failed", 0, "LLM failed"))
                    evaluated_match_types.append("Maybe")
                continue

            blocks = [b.strip() for b in raw_text.split("---EVAL---") if b.strip()]
            for i, job in enumerate(chunk):
                block = blocks[i] if i < len(blocks) else ""
                target_ws = job.get("_worksheet") or worksheet
                if target_ws not in updates_by_ws: updates_by_ws[target_ws] = []
                
                if block:
                    parsed = self.parse_evaluation(block)
                    match_type, rec, h1b, loc, missing, reasoning, salary, tech, score = parsed
                    
                    # FALLBACK CALCULATION: If LLM failed score or was 0, use metrics
                    if score == 0:
                        jd_link = job.get("Job Link") or ""
                        current_jd = self.sheets_client.get_jd_for_url(jd_link) or ""
                        score = self._compute_fallback_score(current_jd, job.get("Location") or "")

                    # Tiered Verdict Mapping (single source of truth)
                    match_type = score_to_verdict(score)

                    # Update all caches
                    eval_results = {
                        "h1b": h1b,
                        "missing_skills": missing,
                        "salary": salary,
                        "tech_stack": tech,
                        "recommended_resume": rec,
                        "score": score
                    }
                    self.update_sponsorship_cache(job.get("Company"), h1b)
                    self.update_intelligence_caches(job, eval_results)
                    
                    updates_by_ws[target_ws].append((job["_row_index"], match_type, rec, h1b, loc, missing, score, reasoning))
                    evaluated_match_types.append(match_type)
                    print(f"    ✅ Eval complete: {job.get('Role Title')} -> {match_type} ({score})")
                else:
                    fallback = "❌ No"
                    updates_by_ws[target_ws].append((job["_row_index"], fallback, "Unknown", "N/A", "N/A", "Parse failed", 0, "Parse failed"))
                    evaluated_match_types.append(fallback)

            # --- PERIODIC SYNC (Every 2 jobs to show immediate progress) ---
            for ws, batch in updates_by_ws.items():
                if len(batch) >= 2:
                    print(f"\n  -> Periodic Sync: Updating {len(batch)} jobs in '{ws.title}'...")
                    self.sheets_client.update_evaluated_jobs(ws, batch)
                    batch.clear() 

        # 3. Final Batch Save
        if updates_by_ws:
            print("\nSaving all evaluations to Google Sheets...")
            for ws, batch in updates_by_ws.items():
                if batch:
                    print(f"  Updating {len(batch)} jobs in '{ws.title}'...")
                    self.sheets_client.update_evaluated_jobs(ws, batch)

        # 4. Save and Summarize
        self.save_all_caches()

        high_priority_count = 0
        if evaluated_match_types:
            dist = Counter(evaluated_match_types)
            high_priority_count = dist.get("🔥 Auto-Apply", 0) + dist.get("✅ Strong Match", 0)
            
            total = len(evaluated_match_types)
            print("\n--- Match Type distribution ---")
            labels = ["🔥 Auto-Apply", "✅ Strong Match", "⚖️ Worth Considering", "❌ No", "Already seen"]
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
        return high_priority_count


    def save_batch_if_needed(self, updates_list, worksheet, batch_size=25):
        """Helper to save in batches to avoid losing progress and reduce API calls."""
        if len(updates_list) >= batch_size:
            print(f"  -> Saving batch of {batch_size} to Google Sheets...")
            self.sheets_client.update_evaluated_jobs(worksheet, updates_list)
            updates_list.clear() # clear list in place

if __name__ == "__main__":
    evaluator = JobEvaluator()
    evaluator.evaluate_all()
