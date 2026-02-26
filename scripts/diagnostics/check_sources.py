import sys
import os
from collections import Counter

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.google_sheets_client import GoogleSheetsClient

def check_source_distribution():
    client = GoogleSheetsClient()
    rows = client.get_all_jobs()
    
    source_counts = Counter(r.get("Source") for r in rows)
    print(f"\n--- Source Distribution for {client.sheet.title} ---")
    for source, count in source_counts.items():
        print(f"  {source or '[Empty]'}: {count}")
    
    # Check a few specific jobs to see their URLs
    print("\nSample Job Links:")
    for r in rows[:5]:
        print(f"  {r.get('Role Title')} -> {r.get('Job Link')}")

if __name__ == "__main__":
    check_source_distribution()
