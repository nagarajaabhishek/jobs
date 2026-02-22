from src.agents.evaluate_jobs import JobEvaluator
import os

def test_optimizations():
    print("--- Verifying Pipeline Optimizations ---")
    evaluator = JobEvaluator()
    
    # 1. Check Role Summaries (Deep Match)
    print(f"\n1. Role Summaries Loaded: {len(evaluator.role_summaries)}")
    for role, summary in evaluator.role_summaries.items():
        print(f"   - {role}: {len(summary)} chars")
        if "SPECIALIZATION" not in summary:
            print(f"     ❌ Summary for {role} looks incomplete.")
    
    # 2. Check Sponsorship Data
    print(f"\n2. Sponsorship Database: {len(evaluator.sponsors)} entries")
    test_companies = ["Google", "Siemens", "Verified Credentials", "Unknown Inc"]
    for company in test_companies:
        result = evaluator.get_verified_sponsorship(company)
        print(f"   - {company}: {result}")

    # 3. Check Strategic Priority
    print(f"\n3. Strategic Priorities")
    test_locs = ["Dallas, TX", "Austin, Texas", "Remote", "Dubai, UAE", "London, UK"]
    for loc in test_locs:
        priority = evaluator.get_strategic_priority(loc)
        print(f"   - {loc}: {priority}")

    # 4. Check Prompt Grounding
    grounded = evaluator.load_user_profiles() # This would be called in evaluate_all
    # But wait, evaluate_all builds the grounded_sys_prompt too.
    # Let's check how the final prompt is constructed.
    sys_prompt = evaluator.load_system_prompt()
    role_specs_text = "\n\n".join(evaluator.role_summaries.values())
    final_grounded = f"{sys_prompt}\n\n### USER PROFILE SUMMARY\n{grounded}\n\n### ROLE-SPECIFIC SPECIALIZATIONS\n{role_specs_text}"
    
    if "ROLE-SPECIFIC SPECIALIZATIONS" in final_grounded:
        print("\n✅ SUCCESS: Final grounded prompt includes specialization data.")
    else:
        print("\n❌ FAILURE: Grounded prompt is missing specialization data.")

if __name__ == "__main__":
    test_optimizations()
