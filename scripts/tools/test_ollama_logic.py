from src.agents.evaluate_jobs import JobEvaluator
evaluator = JobEvaluator()
sys_prompt = evaluator.load_system_prompt()
profile = evaluator.load_user_profiles()
job_context = "Job Title: Product Manager\nCompany: Tech Corp\nLocation: Remote\nJob Description: Looking for a PM with Agile, Stakeholder Management, PRDs, Roadmap, and User Research experience."

raw_text, engine = evaluator.llm.generate_content(
    system_prompt=f"{sys_prompt}\n\n### USER PROFILE\n{profile}",
    user_prompt=f"### JOB POSTING\n{job_context}"
)
print("--- RAW OUTPUT ---")
print(raw_text)
match_type, recommended, h1b, loc_ver, missing, reasoning = evaluator.parse_evaluation(raw_text)
print(f"--- PARSED ---")
print(f"Match Type: {match_type}")
print(f"Recommended: {recommended}")
