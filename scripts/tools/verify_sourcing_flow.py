import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.agents.sourcing_agent import SourcingAgent
from src.core.google_sheets_client import GoogleSheetsClient

def test_real_sourcing_flow():
    print("--- Verifying Fix: Real-world Sourcing Subset ---")
    client = GoogleSheetsClient()
    agent = SourcingAgent(client)
    
    # Tiny subset: One role, one location
    queries = ["Product Manager"]
    locations = {"Dallas, TX": 5}
    
    print(f"Scraping JobSpy for {queries} in {locations} with AI Filter ENABLED...")
    # Using scrape_jobspy_parallel to mimic the real pipeline flow
    total_found = agent.scrape_jobspy_parallel(
        queries=queries, 
        locations=locations, 
        max_workers=1,
        use_ai_filter=True
    )
    
    print(f"\nVerification Complete. Jobs found: {total_found}")
    print("Check your Google Sheet 'Daily Jobs' for new 'Product Manager' entries in Dallas.")

if __name__ == "__main__":
    test_real_sourcing_flow()
