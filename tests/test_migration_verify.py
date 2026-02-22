from src.agents.evaluate_jobs import JobEvaluator
import os

def test_migration():
    print("--- Verifying Data Migration ---")
    evaluator = JobEvaluator()
    print(f"Profile Directory: {evaluator.profiles_dir}")
    print(f"Master Profile Path: {evaluator.master_profile_path}")
    
    if "Job_Automation/data/profiles" in evaluator.profiles_dir:
        print("✅ SUCCESS: JobEvaluator is using the local data/profiles directory.")
    else:
        print("❌ FAILURE: JobEvaluator is NOT using the local data/profiles directory.")
        
    if os.path.exists(evaluator.master_profile_path):
        print(f"✅ SUCCESS: Master profile found at {evaluator.master_profile_path}")
    else:
        print(f"❌ FAILURE: Master profile NOT found at {evaluator.master_profile_path}")
        
    # Check if load_user_profiles returns content
    content = evaluator.load_user_profiles()
    if "USER PROFESSIONAL SUMMARY" in content:
        print("✅ SUCCESS: Profile content loaded and summarized correctly.")
    else:
        print("❌ FAILURE: Failed to load or summarize profile content.")

if __name__ == "__main__":
    test_migration()
