import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.google_sheets_client import GoogleSheetsClient

def check_sheet_status():
    client = GoogleSheetsClient()
    new_jobs, ws = client.get_new_jobs()
    
    evaluated = [j for j in new_jobs if j.get("Match Type") and j.get("Match Type") != "—"]
    unevaluated = [j for j in new_jobs if not j.get("Match Type") or j.get("Match Type") == "—"]
    
    print(f"\n--- Sheet Status: {ws.title} ---")
    print(f"Total rows found: {len(new_jobs)}")
    print(f"Already Evaluated: {len(evaluated)}")
    print(f"Pending Evaluation: {len(unevaluated)}")
    
    if evaluated:
        print("\nSample Evaluated Jobs:")
        for j in evaluated[:3]:
            print(f"  - {j.get('Role Title')} ({j.get('Match Type')})")

if __name__ == "__main__":
    check_sheet_status()
