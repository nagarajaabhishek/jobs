
import os
import sys
import logging
from datetime import datetime

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.agents.sourcing_agent import SourcingAgent
from src.agents.evaluate_jobs import JobEvaluator
from src.core.google_sheets_client import GoogleSheetsClient

def run_production_mvp():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    print("\n--- JobsProof.com | Production MVP Run ---")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Sourcing
    print("\n[Step 1/2] Sourcing Fresh Roles (Texas & Dubai)...")
    sheets_client = GoogleSheetsClient()
    sourcing = SourcingAgent(sheets_client=sheets_client)
    
    # Queries targeted to user preferences
    queries = [
        ("Product Manager associate", "Texas"),
        ("Technical Program Manager entry level", "Texas"),
        ("Business Analyst associate", "Texas"),
        ("Product Owner", "Dubai"),
        ("Product Manager associate", "Dubai")
    ]
    
    total_found = 0
    # Run combined sourcing for USA and Dubai
    print("  Searching for USA and Dubai/UAE roles...")
    jobs = sourcing.scrape(
        queries=["Product Manager", "Technical Program Manager", "Business Analyst", "Product Owner"],
        locations=["United States", "Dubai", "UAE"],
        results_wanted=150
    )
    total_found += len(jobs)
    
    print(f"  Sourcing complete. Total jobs found: {total_found}")
    
    # 2. Evaluation
    print("\n[Step 2/2] Evaluating and Scoring Jobs...")
    evaluator = JobEvaluator()
    # evaluate_all handles fetching NEW jobs from the sheet and scoring them
    high_conviction_count = evaluator.evaluate_all(mode="NEW", limit=50)
    
    print("\n--- Production Run Summary ---")
    print(f"  Total Jobs Found: {total_found}")
    print(f"  Must-Apply / Strong Matches Identified: {high_conviction_count}")
    print("\nView your results in Google Sheets: 'Resume_Agent_Jobs'")

if __name__ == "__main__":
    run_production_mvp()
