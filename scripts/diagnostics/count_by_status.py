import sys
import os
from collections import Counter

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.google_sheets_client import GoogleSheetsClient

def count_by_status():
    client = GoogleSheetsClient()
    rows = client.get_all_jobs()
    
    status_counts = Counter(r.get("Status") for r in rows)
    print(f"\n--- Status Counts for {client.sheet.title} ---")
    for status, count in status_counts.items():
        print(f"  {status or '[Empty]'}: {count}")
    
    # Also check if Match Type is filled for any NEW jobs (unlikely but possible)
    match_with_new = [r for r in rows if r.get("Status") == "NEW" and r.get("Match Type") and r.get("Match Type") != "—"]
    if match_with_new:
        print(f"\n  ⚠ Found {len(match_with_new)} jobs marked 'NEW' but with a Match Type!")

if __name__ == "__main__":
    count_by_status()
