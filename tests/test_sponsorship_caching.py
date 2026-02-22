import os
import yaml
from src.agents.evaluate_jobs import JobEvaluator

def test_sponsorship_caching():
    print("--- Testing Sponsorship Cache Feedback Loop ---")
    evaluator = JobEvaluator()
    evaluator.sponsors_path = "data/sponsors_test.yaml" # Use a test file
    evaluator.sponsors = {}
    evaluator.cache_updated = False
    
    # 1. Test "Likely" sponsorship update
    print("\n1. Testing 'Likely' status...")
    evaluator.update_sponsorship_cache("TestCo", "Likely: Found in JD")
    if evaluator.sponsors.get("TestCo") == "Sponsors (Learned from JD)":
        print("✅ Cache updated internally.")
    else:
        print("❌ Cache update failed.")
        
    # 2. Test "Unlikely" sponsorship update
    print("\n2. Testing 'Unlikely' status...")
    evaluator.update_sponsorship_cache("NoSponsorCorp", "Unlikely: No visa support mentioned")
    if evaluator.sponsors.get("NoSponsorCorp") == "Does Not Sponsor (Learned from JD)":
        print("✅ Cache updated internally.")
    else:
        print("❌ Cache update failed.")

    # 3. Test saving to file
    print("\n3. Testing save to file...")
    evaluator.save_sponsorship_cache()
    if os.path.exists("data/sponsors_test.yaml"):
        with open("data/sponsors_test.yaml", "r") as f:
            content = yaml.safe_load(f)
            if content.get("TestCo") == "Sponsors (Learned from JD)" and content.get("NoSponsorCorp") == "Does Not Sponsor (Learned from JD)":
                print("✅ PASSED: Cache saved correctly to YAML.")
            else:
                print("❌ FAILED: YAML content mismatch.")
        os.remove("data/sponsors_test.yaml")
    else:
        print("❌ FAILED: YAML file not created.")

if __name__ == "__main__":
    test_sponsorship_caching()
