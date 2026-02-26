import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.agents.evaluate_jobs import JobEvaluator

def test_raw_eval():
    evaluator = JobEvaluator()
    # Mocking a job
    job = {
        "Role Title": "Product Manager",
        "Company": "Test Company",
        "Location": "United States",
        "Job Description": "We are looking for a Product Manager with Python and SQL experience.",
        "url": "http://example.com"
    }
    
    # Ground the prompts
    sys_prompt = evaluator.load_system_prompt()
    profiles_prompt = evaluator.load_user_profiles()
    role_specs_text = "\n\n".join(evaluator.role_summaries.values())
    grounded_sys_prompt = f"{sys_prompt}\n\n### USER PROFILE SUMMARY\n{profiles_prompt}\n\n### ROLE-SPECIFIC SPECIALIZATIONS (Use for Deep Matching)\n{role_specs_text}"
    
    job_context = f"Company: {job.get('Company')}\nTitle: {job.get('Role Title')}\nJD: {job.get('Job Description')}"
    
    print("\n--- Requesting Raw LLM Output (Simulating JSON) ---")
    # We simulate what the new prompt expects
    raw_text = """
    {
      "location_verification": "Confirmed: USA",
      "h1b_sponsorship": "Likely",
      "recommended_resume": "Product Manager (TPM)",
      "reasoning": "Standardization is working! Deep analysis of Python/SQL fit.",
      "salary_range": "$130k",
      "tech_stack": ["Python", "SQL"],
      "skill_gaps": ["React"],
      "apply_conviction_score": 90,
      "verdict": "🔥 Auto-Apply"
    }
    """
    
    parsed = evaluator.parse_evaluation(raw_text)
    print(f"Parsed Match Type: {parsed[0]}")
    print(f"Parsed Reasoning: {parsed[5]}")
    print(f"Parsed Score: {parsed[8]}")

if __name__ == "__main__":
    test_raw_eval()
