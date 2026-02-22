import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.agents.evaluate_jobs import JobEvaluator
from src.core.google_sheets_client import GoogleSheetsClient

def run_evaluation_only():
    print("\n--- Starting Evaluation-Only Run ---\n")
    
    # 1. Initialize Evaluator
    evaluator = JobEvaluator()
    
    # 2. Run Evaluation on "NEW" jobs
    print("Evaluating 'NEW' jobs in sheet...")
    evaluator.evaluate_all(mode="NEW")
    
    # 3. Final Sorting
    print("\n--- Final Sorting ---")
    client = GoogleSheetsClient()
    client.sort_daily_jobs()
    
    print("\n--- Evaluation Only Run Complete ---")

if __name__ == "__main__":
    run_evaluation_only()
