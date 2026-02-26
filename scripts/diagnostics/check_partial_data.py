import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.google_sheets_client import GoogleSheetsClient

def check_for_partial_data():
    client = GoogleSheetsClient()
    rows = client.get_all_jobs()
    
    partial = []
    for i, r in enumerate(rows):
        mt = str(r.get("Match Type", "")).strip()
        score = str(r.get("Apply Score", "")).strip()
        if mt and mt != "—" or (score and score != "0"):
            partial.append({
                "Role": r.get("Role Title"),
                "Match Type": mt,
                "Score": score,
                "Status": r.get("Status")
            })
    
    if partial:
        print(f"\n--- Found {len(partial)} jobs with partial data ---")
        for p in partial[:10]:
            print(f"  {p['Role']} | Status: {p['Status']} | Match: {p['Match Type']} | Score: {p['Score']}")
    else:
        print("\nNo jobs have Match Type or Score data yet.")

if __name__ == "__main__":
    check_for_partial_data()
