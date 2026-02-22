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


class JobEvaluator:
    def __init__(self):
        self.sheets_client = GoogleSheetsClient()
        self.llm = LLMRouter()
        self.prompt_path = "src/prompts/gemini_job_fit_analyst.md"
        self.roles = ["TPM", "PO", "Business Analyst", "Scrum Master", "Manager", "GTM"]

        # Profile path: env MASTER_PROFILE_PATH (full path) or PROFILE_DIR (dir containing master_context.yaml)
        master_path = os.environ.get("MASTER_PROFILE_PATH")
        if master_path and os.path.isfile(master_path):
            self.master_profile_path = master_path
            self.profiles_dir = os.path.dirname(master_path)
        else:
            profile_dir = os.environ.get("PROFILE_DIR", "/Users/abhisheknagaraja/Documents/Resume_Agent/.agent/data/Abhishek/")
            self.profiles_dir = profile_dir.rstrip(os.sep)
            self.master_profile_path = os.path.join(self.profiles_dir, "master_context.yaml")


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
        recommended = "General"
        resume_match = re.search(r"\*\*Recommended Resume\*\*\s*\n*(.*?)(?=\n\n|\n\*\*|$)", text, re.DOTALL | re.IGNORECASE)
        if resume_match:
            recommended = resume_match.group(1).strip()
            # Clean up potential extra markers from Ollama
            recommended = recommended.replace('[', '').replace(']', '')
            
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

        return match_type, recommended, h1b_status, loc_ver, skills, reasoning


    def evaluate_all(self, mode="NEW", limit=None):
        eval_cfg = get_evaluation_config()
        if limit is None:
            limit = eval_cfg.get("limit", 300)
        sheet_batch_size = eval_cfg.get("sheet_batch_size", SHEET_BATCH_SIZE_DEFAULT)
        batch_size = eval_cfg.get("batch_eval_size", BATCH_EVAL_SIZE_DEFAULT)

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
        sys_prompt = self.load_system_prompt()
        profiles_prompt = self.load_user_profiles()
        grounded_sys_prompt = f"{sys_prompt}\n\n### USER PROFILE SUMMARY (GROUND TRUTH)\n{profiles_prompt}"
        profile_keywords = self.get_profile_skill_keywords()
        updates = []
        evaluated_match_types = []

        # --- 0. DUPLICATE / ALREADY-SEEN: skip jobs already evaluated or applied (any tab) ---
        to_eval = []
        for job in new_jobs:
            canonical = normalize_job_url(job.get("Job Link") or job.get("url") or "")
            if canonical and canonical in already_seen:
                print(f"  Skip (already seen/applied): {job.get('Role Title')} at {job.get('Company')}")
                updates.append((
                    job["_row_index"],
                    "Already seen",
                    "—",
                    "N/A",
                    "N/A",
                    "Duplicate of previously evaluated or applied job; not re-evaluated.",
                ))
                evaluated_match_types.append("Already seen")
                self.save_batch_if_needed(updates, worksheet, batch_size=sheet_batch_size)
                continue
            to_eval.append(job)
        new_jobs = to_eval
        to_eval = []

        # --- 1. FAST FILTER: collect jobs that need LLM vs. reject immediately ---
        for job in new_jobs:
            if mode == "NEW":
                passed, reject_reason = self.passes_initial_filter(job)
                if not passed:
                    print(f"  Filtered: {job.get('Role Title')} at {job.get('Company')} -> {reject_reason}")
                    updates.append((
                        job["_row_index"],
                        "Not at all",
                        "None (Filtered)",
                        "N/A",
                        "N/A",
                        reject_reason,
                    ))
                    evaluated_match_types.append("Not at all")
                    continue
            to_eval.append(job)

        self.save_batch_if_needed(updates, worksheet, batch_size=sheet_batch_size)

        # --- 2. BATCH LLM EVALUATION: process to_eval in chunks ---
        for chunk_start in range(0, len(to_eval), batch_size):
            chunk = to_eval[chunk_start : chunk_start + batch_size]
            job_contexts = []
            for i, job in enumerate(chunk):
                jd_text = (job.get("Job Description") or "").strip()
                job_link = job.get("Job Link") or job.get("url") or ""
                if not jd_text:
                    logging.warning(
                        "Empty Job Description for '%s' at %s (row %s). Fit quality may be lower. Consider re-sourcing with full JD.",
                        job.get("Role Title"), job.get("Company"), job.get("_row_index"),
                    )
                    jd_text = f"[No description available.] Estimate fit from title/location only. Job Link: {job_link}"
                overlap = self.count_skill_overlap(jd_text, profile_keywords)
                nudge = ""
                if overlap >= 5:
                    nudge = "\n[Pre-check: This JD contains 5+ skills from the profile. You MUST rate at least Worth Trying. Do NOT use Maybe.]"
                job_contexts.append(
                    f"### JOB POSTING {i + 1}\n"
                    f"Job Title: {job.get('Role Title')}\nCompany: {job.get('Company')}\n"
                    f"Location: {job.get('Location')}\nJob Description: {jd_text}{nudge}"
                )
            user_prompt = "\n\n".join(job_contexts)
            if len(chunk) > 1:
                user_prompt += (
                    "\n\n---\nEvaluate each job above. For each job output the same Markdown format "
                    "(Recommended Resume, Match Type, Reasoning, Skill Gap Summary). "
                    "Separate each job's evaluation with exactly: ---EVAL---"
                )

            print(f"  Batch evaluating jobs {chunk_start + 1}-{chunk_start + len(chunk)}/{len(to_eval)}...")
            raw_text, engine_used = self.llm.generate_content(
                system_prompt=grounded_sys_prompt,
                user_prompt=user_prompt,
            )

            if engine_used == "FAILED":
                for job in chunk:
                    updates.append((job["_row_index"], "Maybe", "Unknown", "N/A", "N/A", "LLM failed"))
                    evaluated_match_types.append("Maybe")
                self.save_batch_if_needed(updates, worksheet, batch_size=sheet_batch_size)
                continue

            # Split by ---EVAL--- and parse each block (same order as chunk)
            blocks = [b.strip() for b in raw_text.split("---EVAL---") if b.strip()]
            for i, job in enumerate(chunk):
                block = blocks[i] if i < len(blocks) else ""
                jd_text = job.get("Job Description", "") or ""
                overlap = self.count_skill_overlap(jd_text, profile_keywords)
                if block:
                    match_type, recommended, h1b, loc_ver, missing, reasoning = self.parse_evaluation(block)
                    # Calibration override: 5+ skill overlap but model said Maybe → upgrade to Worth Trying
                    if overlap >= 5 and match_type == "Maybe":
                        match_type = "Worth Trying"
                        missing = (missing or "") + " [Auto-upgraded from Maybe: 5+ skill overlap]"
                    updates.append((job["_row_index"], match_type, recommended, h1b, loc_ver, missing))
                    evaluated_match_types.append(match_type)
                    print(f"    -> {job.get('Role Title')}: {match_type} | {recommended}")
                else:
                    # No parse: if high overlap, still give Worth Trying
                    fallback = "Worth Trying" if overlap >= 5 else "Maybe"
                    updates.append((job["_row_index"], fallback, "Unknown", "N/A", "N/A", "No parse" if fallback == "Maybe" else "Parse failed; 5+ overlap"))
                    evaluated_match_types.append(fallback)
                    print(f"    -> {job.get('Role Title')}: {fallback} (no parse)")
                self.save_batch_if_needed(updates, worksheet, batch_size=sheet_batch_size)

        if updates:
            print("\nUpdating remaining evaluations to Google Sheets...")
            self.sheets_client.update_evaluated_jobs(worksheet, updates)

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
