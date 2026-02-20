import os
import re
import yaml
import time
from google import genai
from google_sheets_client import GoogleSheetsClient
from dotenv import load_dotenv

load_dotenv()
from llm_router import LLMRouter

class JobEvaluator:
    def __init__(self):
        self.sheets_client = GoogleSheetsClient()
        self.llm = LLMRouter()
        
        # Paths
        self.prompt_path = "/Users/abhisheknagaraja/Documents/Resume_Agent/commands/prompts/gemini_job_fit_analyst.md"
        self.profiles_dir = "/Users/abhisheknagaraja/Documents/Resume_Agent/.agent/data/Abhishek/"
        
        # 6 Baseline Roles
        self.role_files = [
            "role_tpm.yaml",
            "role_po.yaml",
            "role_business_analyst.yaml",
            "role_sm.yaml",
            "role_manager.yaml",
            "role_gtm.yaml"
        ]

    def passes_initial_filter(self, job):
        """
        Fast, rule-based filter to skip obviously bad jobs before sending to LLM.
        Returns (True, "") if it passes, or (False, "Reason") if it fails.
        """
        title = str(job.get('Role Title', '')).lower()
        desc = str(job.get('url', '')).lower() # In case the JD isn't available, we fallback to searching the URL string
        
        # 1. Skip overly senior roles
        senior_keywords = ["senior", "sr", "sr.", "staff", "principal", "director", "vp", "head of", "lead"]
        for keyword in senior_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', title):
                return False, f"Skip: Senior/Lead Role ({keyword})"
                
        # 2. Skip roles requiring security clearance (if you don't have one)
        clearance_keywords = ["clearance", "ts/sci", "secret clearance", "top secret"]
        for keyword in clearance_keywords:
            if keyword in title or keyword in desc:
                return False, "Skip: Requires Security Clearance"
                
        # 3. Skip unrelated fields that might slip into search results
        unrelated_keywords = [
            "nurse", "registered nurse", "rn", "physician", "driver", "cdl", 
            "warehouse", "mechanic", "cashier", "architect", "software engineer",
            "backend", "frontend", "fullstack", "full stack", "account executive", "recruiter"
        ]
        for keyword in unrelated_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', title):
                return False, f"Skip: Unrelated Field ({keyword})"

        # 4. Filter by years of experience if available in a basic text match (e.g. "8+ years")
        # (This is harder without the full JD, but we can catch obvious ones if they are in the short description)
        
        return True, ""

    def load_system_prompt(self):
        with open(self.prompt_path, 'r') as f:
            return f.read()

    def load_user_profiles(self):
        profiles_content = ""
        for role_file in self.role_files:
            file_path = os.path.join(self.profiles_dir, role_file)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = yaml.safe_load(f)
                    profiles_content += f"\n\n--- FILE: {role_file} ---\n{yaml.dump(content)}\n"
            else:
                if "business_analyst" in role_file:
                    alt_path = os.path.join(self.profiles_dir, "role_ba.yaml")
                    if os.path.exists(alt_path):
                        with open(alt_path, 'r') as f:
                            content = yaml.safe_load(f)
                            profiles_content += f"\n\n--- FILE: role_ba.yaml ---\n{yaml.dump(content)}\n"
        return profiles_content

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
        match_type = "Unknown"
        # Search for strict header first
        type_match = re.search(r"-\s*\*\*(Not at all|Maybe|Ambitious|Worth Trying|For sure)\*\*", raw_text, re.IGNORECASE)
        if type_match:
            match_type = type_match.group(1).strip()
        else:
            # Fallback search for loose bullet points or conversational text
            priority_ranking = ["For sure", "Worth Trying", "Ambitious", "Maybe", "Not at all"]
            for t in priority_ranking:
                # Use regex to find whole phrases even if they have extra asterisks
                if re.search(r"\b" + re.escape(t) + r"\b", raw_text, re.IGNORECASE):
                    match_type = t
                    break

        missing = "Unknown"
        skill_match = re.search(r"\*\*Skill Gap Summary\*\*\s*\n+(.*)", raw_text, re.IGNORECASE)
        if skill_match:
            missing = skill_match.group(1).strip()

        return match_type, recommended, missing

    def evaluate_all(self):
        print("Fetching NEW jobs from Google Sheets...")
        new_jobs, worksheet = self.sheets_client.get_new_jobs(limit=300)
        
        if not new_jobs:
            print("No new jobs to evaluate!")
            return

        print(f"Found {len(new_jobs)} jobs. Loading Context...")
        sys_prompt = self.load_system_prompt()
        profiles_prompt = self.load_user_profiles()
        
        updates = []
        
        for idx, job in enumerate(new_jobs):
            print(f"Evaluating {idx+1}/{len(new_jobs)}: {job.get('Role Title')} at {job.get('Company')}...")
            
            # --- 1. FAST FILTER (The Bouncer) ---
            passed, reject_reason = self.passes_initial_filter(job)
            if not passed:
                print(f"  -> {reject_reason}")
                updates.append((
                    job['_row_index'], 
                    "Not at all",              # Match Type
                    "None (Filtered)",         # Recommended Resume
                    reject_reason              # Missing Skills / Reason
                ))
                self.save_batch_if_needed(updates, worksheet)
                continue

            # --- 2. DEEP EVALUATION (The LLM) ---
            job_context = f"Job Title: {job.get('Role Title')}\nCompany: {job.get('Company')}\nLocation: {job.get('Location')}\n--- Note: We only have limited JD text if fetched via generic scraping, please estimate fit based on available title/company if description is sparse: {job.get('url')} ---"
            
            full_prompt = f"{sys_prompt}\n\n### USER PROFILES\n{profiles_prompt}\n\n### JOB POSTING\n{job_context}"
            
            raw_text, engine_used = self.llm.generate_content(
                system_prompt=sys_prompt,
                user_prompt=f"### USER PROFILES\n{profiles_prompt}\n\n### JOB POSTING\n{job_context}"
            )
            
            if engine_used == "FAILED":
                print(f"  -> {job.get('Role Title')} failed on all 3 tiers. Skipping.")
                continue
            
            match_type, recommended, missing = self.parse_evaluation(raw_text)
            print(f"  -> ({engine_used}) Match: {match_type} | Resume: {recommended}")
            
            updates.append((
                job['_row_index'], 
                match_type, 
                recommended, 
                missing
            ))
            
            self.save_batch_if_needed(updates, worksheet)
                
        # Final flush of any remaining jobs
        if updates:
            print("\nUpdating remaining evaluations to Google Sheets...")
            self.sheets_client.update_evaluated_jobs(worksheet, updates)
            
        print("\nDone! Sorting the Google Sheet by match priority...")
        self.sheets_client.sort_daily_jobs()

    def save_batch_if_needed(self, updates_list, worksheet):
        """Helper to save in batches to avoid losing progress and keep the loop clean."""
        if len(updates_list) >= 10:
            print("  -> Saving batch of 10 to Google Sheets...")
            self.sheets_client.update_evaluated_jobs(worksheet, updates_list)
            updates_list.clear() # clear list in place

if __name__ == "__main__":
    evaluator = JobEvaluator()
    evaluator.evaluate_all()
