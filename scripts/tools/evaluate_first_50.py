import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.agents.evaluate_jobs import JobEvaluator


def run_test_evaluation():
    print("--- 🚀 Starting Efficient 50-Job Evaluation Test ---")
    print("This will evaluate the first 50 'NEW' jobs in the sheet using the ")
    print("most cost-effective Gemini model configured (gemini-2.5-flash-lite).\n")
    
    evaluator = JobEvaluator()
    evaluator.evaluate_all(mode="NEW", limit=10)
    
    print("\n--- ✅ Evaluation Complete ---")
    print("Check your Google Sheet for the results, parsed Match Types, and Apply Conviction Scores.")

if __name__ == "__main__":
    run_test_evaluation()
