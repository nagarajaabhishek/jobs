import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.agents.sourcing_agent import SourcingAgent # type: ignore
from src.core.google_sheets_client import GoogleSheetsClient # type: ignore

def test_manual_resolution():
    client = GoogleSheetsClient()
    agent = SourcingAgent(client)
    
    # Use a real URL that is likely to have a JD (e.g., a Lever or Greenhouse link)
    test_urls = [
        "https://jobs.lever.co/google/672776c5-ee32-4d26-9d84-90e8790327f3", # Random Lever link
        "https://boards.greenhouse.io/openai/jobs/4207198005" # Random Greenhouse link
    ]
    
    print("--- 🧪 Testing Manual JD Resolution Fallback ---")
    for url in test_urls:
        print(f"\nTarget: {url}")
        content = agent._fetch_jd_manually(url)
        if content:
            print(f"SUCCESS! Extracted {len(content)} characters.")
            print("Snippet: " + content[:200].replace('\n', ' ') + "...")
        else:
            print("FAILED to extract content.")

if __name__ == "__main__":
    test_manual_resolution()
