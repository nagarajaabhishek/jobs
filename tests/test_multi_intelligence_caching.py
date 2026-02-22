import os
import yaml
from src.agents.evaluate_jobs import JobEvaluator

def test_multi_intelligence_caching():
    print("--- Testing Multi-Intelligence Caching Expansion ---")
    evaluator = JobEvaluator()
    
    # Override paths to test files
    evaluator.skill_gaps_path = "data/skill_gaps_test.yaml"
    evaluator.salary_benchmarks_path = "data/salary_test.yaml"
    evaluator.company_insights_path = "data/company_test.yaml"
    evaluator.sponsors_path = "data/sponsors_test.yaml"
    
    # Initialize empty test data
    evaluator.skill_gaps = {}
    evaluator.salary_benchmarks = {}
    evaluator.company_insights = {}
    evaluator.sponsors = {}
    evaluator.cache_updated = False
    
    # Mock data
    job_data = {"Company": "TechFlow AI", "Location": "Austin, TX"}
    eval_results = {
        "h1b": "Likely: Sponsor",
        "missing_skills": "Kubernetes, Go, GCP",
        "salary": "$140k - $180k",
        "tech_stack": "Python, AWS, React",
        "recommended_resume": "Product Manager (TPM)"
    }
    
    print("\n1. Updating caches with mock data...")
    evaluator.update_sponsorship_cache(job_data["Company"], eval_results["h1b"])
    evaluator.update_intelligence_caches(job_data, eval_results)
    
    # Verify internal state
    if evaluator.skill_gaps.get("kubernetes") == 1 and evaluator.skill_gaps.get("go") == 1:
        print("✅ Skill gaps tracked correctly.")
    else:
        print(f"❌ Skill gap tracking failed: {evaluator.skill_gaps}")
        
    if evaluator.salary_benchmarks.get("Product Manager (TPM)", {}).get("Austin, TX") == "$140k - $180k":
        print("✅ Salary benchmarks tracked correctly.")
    else:
        print("❌ Salary tracking failed.")
        
    if "Python" in evaluator.company_insights.get("TechFlow AI", {}).get("tech_stack", []):
        print("✅ Company tech stack tracked correctly.")
    else:
        print("❌ Tech stack tracking failed.")

    # 2. Testing persistence
    print("\n2. Testing cache persistence...")
    evaluator.save_all_caches()
    
    files_to_check = [evaluator.skill_gaps_path, evaluator.salary_benchmarks_path, evaluator.company_insights_path]
    all_exist = all(os.path.exists(f) for f in files_to_check)
    
    if all_exist:
        print("✅ All cache files created successfully.")
        # Final Verification of one file content
        with open(evaluator.skill_gaps_path, "r") as f:
            content = yaml.safe_load(f)
            if content.get("kubernetes") == 1:
                print("✅ YAML content verified.")
            else:
                print("❌ YAML content mismatch.")
        
        # Cleanup
        for f in files_to_check + [evaluator.sponsors_path]:
            if os.path.exists(f): os.remove(f)
    else:
        print("❌ Cache files missing.")

if __name__ == "__main__":
    test_multi_intelligence_caching()
