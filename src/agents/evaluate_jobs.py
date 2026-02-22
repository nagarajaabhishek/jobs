import logging
import os
import re
import yaml
from collections import Counter

from src.core.google_sheets_client import GoogleSheetsClient, normalize_job_url
from src.core.llm_router import LLMRouter
from src.core.config import get_evaluation_config
from src.core.job_filters import passes_evaluation_prefilter

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
        eval_cfg = get_evaluation_config()
        ollama_model = eval_cfg.get("ollama_model") or os.environ.get("OLLAMA_MODEL") or "llama3.2"
        self.llm = LLMRouter(model=ollama_model)
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

        # Local migration path: prioritize 'data/' within this repo
        local_profiles = os.path.join(os.getcwd(), "data", "profiles")
        if os.path.isdir(local_profiles):
            self.profiles_dir = local_profiles
            self.master_profile_path = os.path.join(self.profiles_dir, "master_context.yaml")
        else:
            # Fallback path if data/ doesn't exist (legacy/env)
            master_path = os.environ.get("MASTER_PROFILE_PATH")
            if master_path and os.path.isfile(master_path):
                self.master_profile_path = master_path
                self.profiles_dir = os.path.dirname(master_path)
            else:
                profile_dir = os.environ.get("PROFILE_DIR", "/Users/abhisheknagaraja/Documents/Resume_Agent/.agent/data/Abhishek/")
                self.profiles_dir = profile_dir.rstrip(os.sep)
                self.master_profile_path = os.path.join(self.profiles_dir, "master_context.yaml")
        
        # Pre-cache role summaries for Deep Match
        self.role_summaries = self._load_role_summaries()

    def _load_role_summaries(self):
        """Dynamically loads and pre-summarizes all role profiles found in profiles_dir."""
        summaries = {}
        found_roles = []
        
        if not os.path.exists(self.profiles_dir):
            return summaries

        # Scan for all role_*.yaml files
        for filename in os.listdir(self.profiles_dir):
            if filename.startswith("role_") and filename.endswith(".yaml"):
                fpath = os.path.join(self.profiles_dir, filename)
                try:
                    with open(fpath, "r") as f:
                        content = yaml.safe_load(f)
                    
                    # Derive role name from filename or internal name
                    # e.g., role_technical_product_manager.yaml -> Product Manager (TPM)
                    # For now, we'll try to match against our standard set or use a cleaned filename
                    base = filename.replace("role_", "").replace(".yaml", "").replace("_", " ").title()
                    
                    # Map common patterns to our standardized names for better consistency
                    role_name = base
                    if "Tpm" in base or "Technical Product Manager" in base: role_name = "Product Manager (TPM)"
                    elif "Po" in base or "Product Owner" in base: role_name = "Product Owner (PO)"
                    elif "Ba" in base or "Business Analyst" in base: role_name = "Business Analyst (BA)"
                    elif "Sm" in base or "Scrum Master" in base: role_name = "Scrum Master (SM)"
                    elif "Gtm" in base: role_name = "Go-To Market (GTM)"
                    
                    found_roles.append(role_name)
                    
                    # Use simplified summary logic for roles
                    s = f"### {role_name} SPECIALIZATION\n"
                    s += f"Summary: {content.get('summary', 'N/A')}\n"
                    top_skills = []
                    for entry in content.get('skills', [])[:3]:
                        if isinstance(entry, dict):
                            cat = entry.get('category')
                            skills = entry.get('skill_list') or entry.get('skills')
                            top_skills.append(f"{cat}: {skills}")
                    s += f"Key Skills: {'; '.join(top_skills)}\n"
                    summaries[role_name] = s
                except Exception as e:
                    print(f"  ⚠ Error loading profile {filename}: {e}")
        
        self.roles = sorted(list(set(found_roles)))
        return summaries

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

    def summarize_profile(self, profile):
        """Converts complex YAML profile into a high-density Markdown summary for better LLM parsing."""
        summary = "## USER PROFESSIONAL SUMMARY\n\n"
        
        # 1. Experience
        summary += "### TOP EXPERIENCE\n"
        for exp in profile.get('experience', [])[:5]:
            summary += f"- **{exp.get('role')}** at {exp.get('company')} ({exp.get('start_date')} - {exp.get('end_date')})\n"
            summary += f"  * Key: {', '.join(exp.get('bullet_points', [])[:3])}\n"
            
        # 2. Key Skills
        summary += "\n### SKILLS INVENTORY\n"
        skills = profile.get('skills', [])
        if isinstance(skills, list):
            for skill_entry in skills:
                cat = skill_entry.get('category', 'General')
                list_str = skill_entry.get('skill_list', '')
                summary += f"- **{cat}**: {list_str}\n"
        elif isinstance(skills, dict):
            for category, skill_list in skills.items():
                summary += f"- **{category}**: {', '.join(skill_list)}\n"

            
        # 3. Projects (Crucial for evidence)
        summary += "\n### PROJECTS\n"
        for proj in profile.get('projects', [])[:5]:
            summary += f"- **{proj.get('name')}**: {proj.get('description')}\n"
            if proj.get('technologies'):
                summary += f"  * Tech: {', '.join(proj.get('technologies'))}\n"
                
        return summary

    def load_user_profiles(self):
        """Loads and summarizes the master context for evaluation context."""
        if os.path.exists(self.master_profile_path):
            with open(self.master_profile_path, "r") as f:
                content = yaml.safe_load(f)
                summary = self.summarize_profile(content)
                return f"{summary}\n\n### TARGET ROLES AVAILABLE\n{', '.join(self.roles)}"
        print(f"  ⚠ Warning: Master profile not found at {self.master_profile_path}. Set PROFILE_DIR or MASTER_PROFILE_PATH in .env")
        return "Error: Master profile not found. Set PROFILE_DIR or MASTER_PROFILE_PATH."

    def get_profile_skill_keywords(self):
        """Extract searchable skill keywords from the profile for overlap counting. Returns a set of lowercase phrases."""
        keywords = set()
        if not os.path.exists(self.master_profile_path):
            return keywords
        try:
            with open(self.master_profile_path, 'r') as f:
                content = yaml.safe_load(f)
            # From skills
            for entry in content.get("skills", []) if isinstance(content.get("skills"), list) else []:
                list_str = entry.get("skill_list") or entry.get("skills") or ""
                for part in re.split(r"[,;/]", str(list_str)):
                    token = part.strip().lower()
                    if len(token) > 2:
                        keywords.add(token)
            if isinstance(content.get("skills"), dict):
                for skill_list in content["skills"].values():
                    for s in (skill_list or []):
                        if isinstance(s, str) and len(s) > 2:
                            keywords.add(s.strip().lower())
            # From experience bullets
            for exp in content.get("experience", [])[:8]:
                for bullet in exp.get("bullet_points", [])[:5]:
                    for part in re.split(r"[,;.]", str(bullet)):
                        token = part.strip().lower()
                        if 3 <= len(token) <= 40:
                            keywords.add(token)
            # From projects
            for proj in content.get("projects", [])[:5]:
                desc = proj.get("description") or ""
                for part in re.split(r"[,;.]", desc):
                    token = part.strip().lower()
                    if 3 <= len(token) <= 40:
                        keywords.add(token)
        except Exception:
            pass
        return keywords

    def count_skill_overlap(self, jd_text, keywords=None):
        """Count how many profile skill keywords appear in the JD. Used to nudge away from Maybe when >= 5."""
        keywords = keywords or self.get_profile_skill_keywords()
        if not keywords:
            return 0
        jd_lower = (jd_text or "").lower()
        return sum(1 for kw in keywords if kw in jd_lower)



    def parse_evaluation(self, raw_text):
        # 1. Parse Recommended Resume
        recommended = "Unknown"
        # Search for strict header first
        rec_match = re.search(r"\*\*Recommended Resume\*\*\s*\n+([^\n]+)", raw_text, re.IGNORECASE)
        if rec_match:
            recommended = rec_match.group(1).replace("[", "").replace("]", "").replace("*", "").strip()
        else:
            # Fallback search for loose bullet points or conversational text
            for t in ["TPM", "PO", "BA", "SM", "Manager", "GTM"]:
                if re.search(r"\b" + t + r"\b", raw_text, re.IGNORECASE):
                    recommended = t
                    break

        # 2. Parse Match Type
        # 0. Clean and prepare text
        text = raw_text.strip()
        
        # 1. Parse Location Verification
        loc_ver = "Unknown"
        loc_match = re.search(r"\*\*Location Verification\*\*\s*\n*(.*?)(?=\n\n|\n\*\*|$)", text, re.DOTALL | re.IGNORECASE)
        if loc_match:
            loc_ver = loc_match.group(1).strip()

        # 2. Parse H1B Sponsorship
        h1b_status = "Unknown"
        h1b_match = re.search(r"\*\*H1B Sponsorship\*\*\s*\n*(.*?)(?=\n\n|\n\*\*|$)", text, re.DOTALL | re.IGNORECASE)
        if h1b_match:
            h1b_status = h1b_match.group(1).strip()

        # 3. Parse Recommended Resume
        recommended = "Unknown"
        resume_match = re.search(r"\*\*Recommended Resume\*\*\s*\n*(.*?)(?=\n\n|\n\*\*|$)", text, re.DOTALL | re.IGNORECASE)
        if resume_match:
            val = resume_match.group(1).strip()
            # Strict cleaning
            val = val.replace('[', '').replace(']', '').replace('*', '').strip()
            # Check if it matches any of our allowed roles
            for role in self.roles:
                if role.lower() in val.lower() or (re.search(r"\((.*?)\)", role) and re.search(r"\((.*?)\)", role).group(1).lower() in val.lower()):
                    recommended = role
                    break
            if recommended == "Unknown":
                recommended = val # Fallback to LLM output if it doesn't match clean list
            
        # 4. Parse Match Type
        match_type = "Unknown"
        # Search for any line containing "Type" or "Match" followed by one of our categories
        categories = ["For sure", "Worth Trying", "Ambitious", "Maybe", "Not at all"]
        
        # Look for the Category itself anywhere in the text if a strict match fails
        type_found = False
        # Try strict header first
        for header in ["Match Type", "Type", "Fit Type"]:
            pattern = rf"\*\*{header}\*\*\s*\n*(.*?)(?=\n\n|\n\*\*|$)"
            m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if m:
                val = m.group(1).strip().replace('*', '').replace('-', '').strip()
                # Check if the value contains any of our categories
                for cat in categories:
                    if cat.lower() in val.lower():
                        match_type = cat
                        type_found = True
                        break
            if type_found: break
            
        if not type_found:
            # Final fallback: Just look for the keywords in the whole text
            # But only if they appear near the top or bottom to avoid false positives in reasoning
            for cat in categories:
                if re.search(rf"\b{cat}\b", text, re.IGNORECASE):
                    match_type = cat
                    break
        
        if match_type == "Unknown":
            match_type = "Maybe" # Default only if truly nothing found


        # 5. Parse Skill Gaps
        skills = "N/A"
        skills_match = re.search(r"\*\*Skill Gap Summary\*\*\s*\n*(.*?)(?=\n\n|\n\*\*|$)", text, re.DOTALL | re.IGNORECASE)
        if skills_match:
            skills = skills_match.group(1).strip()
            
        # 6. Parse Reasoning (Catch everything between Type/Verdict and Skill Gap Summary)
        reasoning = "N/A"
        reason_match = re.search(r"\*\*Reasoning\*\*\s*\n*(.*?)(?=\n\n|\n\*\*|Skill Gap Summary|$)", text, re.DOTALL | re.IGNORECASE)
        if reason_match:
            reasoning = reason_match.group(1).strip()
            
        # 7. Parse Salary
        salary = "Not mentioned"
        salary_match = re.search(r"\*\*Salary Range\*\*\s*\n*(.*?)(?=\n\n|\n\*\*|$)", text, re.DOTALL | re.IGNORECASE)
        if salary_match:
            salary = salary_match.group(1).strip()
            
        # 8. Parse Tech Stack
        tech_stack = "N/A"
        tech_match = re.search(r"\*\*Tech Stack Identified\*\*\s*\n*(.*?)(?=\n\n|\n\*\*|$)", text, re.DOTALL | re.IGNORECASE)
        if tech_match:
            tech_stack = tech_match.group(1).strip()

        # 9. Parse Apply Conviction Score
        score = 0
        # More robust regex to handle "Score: 85", "Score: 85/100", "score of 85", etc.
        score_patterns = [
            r"Apply Conviction Score:\s*(\d+)",
            r"Score:\s*(\d+)",
            r"score of\s*(\d+)",
            r"Confidence:\s*(\d+)"
        ]
        
        for pattern in score_patterns:
            score_match = re.search(pattern, text, re.IGNORECASE)
            if score_match:
                score = int(score_match.group(1))
                break
        
        # Cleanup score if LLM outputted something like 1000 or -1
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

        print(f"Evaluation backend: Ollama (model: {self.llm.ollama_model})")
        ok, err = self.llm.check_ollama_available()
        if not ok:
            print(f"  ⚠ {err}")
            print("  Continuing anyway; batches will show 'LLM failed' if Ollama is not running.")

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
            raw_text, engine_used = self.llm.generate_content(grounded_sys_prompt, user_prompt)

            if engine_used == "FAILED":
                for job in chunk:
                    target_ws = job.get("_worksheet") or worksheet
                    if target_ws not in updates_by_ws: updates_by_ws[target_ws] = []
                    updates_by_ws[target_ws].append((job["_row_index"], "Maybe", "Unknown", "N/A", "N/A", "LLM failed"))
                    evaluated_match_types.append("Maybe")
                continue

            blocks = [b.strip() for b in raw_text.split("---EVAL---") if b.strip()]
            for i, job in enumerate(chunk):
                block = blocks[i] if i < len(blocks) else ""
                target_ws = job.get("_worksheet") or worksheet
                if target_ws not in updates_by_ws: updates_by_ws[target_ws] = []
                
                if block:
                    parsed = self.parse_evaluation(block)
                    match_type, rec, h1b, loc, missing, reason, salary, tech, score = parsed
                    
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
                    
                    updates_by_ws[target_ws].append((job["_row_index"], match_type, rec, h1b, loc, missing, score))
                    evaluated_match_types.append(match_type)
                    print(f"    -> {job.get('Role Title')}: {match_type} ({score})")
                else:
                    fallback = "❌ No"
                    updates_by_ws[target_ws].append((job["_row_index"], fallback, "Unknown", "N/A", "N/A", "Parse failed", 0))
                    evaluated_match_types.append(fallback)

        # 3. Final Batch Save
        if updates_by_ws:
            print("\nSaving all evaluations to Google Sheets...")
            for ws, batch in updates_by_ws.items():
                if batch:
                    print(f"  Updating {len(batch)} jobs in '{ws.title}'...")
                    self.sheets_client.update_evaluated_jobs(ws, batch)

        # 4. Save and Summarize
        self.save_all_caches()

        # Calibration summary: distribution and Maybe > 80% warning

        # Calibration summary: distribution and Maybe > 80% warning
        if evaluated_match_types:
            dist = Counter(evaluated_match_types)
            total = len(evaluated_match_types)
            print("\n--- Match Type distribution ---")
            for label in ["For sure", "Worth Trying", "Ambitious", "Maybe", "Not at all"]:
                n = dist.get(label, 0)
                pct = (100 * n / total) if total else 0
                print(f"  {label}: {n} ({pct:.0f}%)")
            maybe_pct = (100 * dist.get("Maybe", 0) / total) if total else 0
            if maybe_pct > 80:
                print("\n  ⚠ Calibration warning: >80% of jobs are 'Maybe'. Consider adding few-shot examples or tightening the 5+ skill rule in the prompt.")

        print("\nDone! Sorting the Google Sheet by match priority...")
        self.sheets_client.sort_daily_jobs()


    def save_batch_if_needed(self, updates_list, worksheet, batch_size=25):
        """Helper to save in batches to avoid losing progress and reduce API calls."""
        if len(updates_list) >= batch_size:
            print(f"  -> Saving batch of {batch_size} to Google Sheets...")
            self.sheets_client.update_evaluated_jobs(worksheet, updates_list)
            updates_list.clear() # clear list in place

if __name__ == "__main__":
    evaluator = JobEvaluator()
    evaluator.evaluate_all()
