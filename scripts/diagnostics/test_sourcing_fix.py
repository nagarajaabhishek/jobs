import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.agents.sourcing_agent import SourcingAgent
from src.core.google_sheets_client import GoogleSheetsClient
from src.core.config import get_sourcing_config

def test_sourcing():
    client = GoogleSheetsClient()
    sourcing_agent = SourcingAgent(client)
    cfg = get_sourcing_config()
    
    queries = ["Product Manager"]
    locations = {"United States": 5}
    
    print("\n--- Testing JobSpy Sourcing ---")
    sourcing_agent.scrape_jobspy_parallel(
        queries=queries, 
        locations=locations, 
        max_workers=1,
        use_ai_filter=False
    )
    
    print("\n--- Checking Source Distribution ---")
    rows = client.get_all_jobs()
    sources = {}
    for r in rows:
        s = r.get("Source", "Unknown")
        sources[s] = sources.get(s, 0) + 1
    
    print(f"Sources found: {sources}")

if __name__ == "__main__":
    test_sourcing()
