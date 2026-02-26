import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.google_sheets_client import GoogleSheetsClient

def inspect_sourcing_tags():
    client = GoogleSheetsClient()
    rows = client.get_all_jobs()
    
    tagged = []
    for r in rows:
        tags = str(r.get("Sourcing Tags", "")).strip()
        if tags:
            tagged.append({
                "Role": r.get("Role Title"),
                "Tags": tags
            })
            
    if tagged:
        print(f"\n--- Found {len(tagged)} jobs with Sourcing Tags ---")
        for t in tagged[:10]:
            print(f"  Role: {t['Role']}")
            print(f"  Tags: {t['Tags'][:200]}...") # Show snippet
    else:
        print("\nNo Sourcing Tags found in the current sheet.")

if __name__ == "__main__":
    inspect_sourcing_tags()
