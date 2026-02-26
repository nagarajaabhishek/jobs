import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.google_sheets_client import GoogleSheetsClient

def summarize_matches():
    client = GoogleSheetsClient()
    rows = client.get_all_jobs()
    
    high_conviction = [
        r for r in rows 
        if str(r.get("Match Type", "")).lower().strip().replace("*", "") in ["🔥 auto-apply", "✅ strong match", "for sure"]
    ]
    
    print(f"\n--- 🚀 Today's Top Matches ({len(high_conviction)}) ---")
    for i, r in enumerate(high_conviction[:10]):
        print(f"{i+1}. {r.get('Role Title')} @ {r.get('Company')}")
        print(f"   Score: {r.get('Apply Score')} | Match: {r.get('Match Type')}")
        print(f"   Link: {r.get('Job Link')}\n")

if __name__ == "__main__":
    summarize_matches()
