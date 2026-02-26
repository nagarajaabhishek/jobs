import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.google_sheets_client import GoogleSheetsClient

def check_jd_availability():
    client = GoogleSheetsClient()
    rows = client.get_all_jobs()
    
    evaluated_no_h1b = [
        r for r in rows 
        if r.get("Status") == "EVALUATED" and str(r.get("H1B Sponsorship", "")).lower() in ["unknown", "—", ""]
    ]
    
    print(f"\n--- H1B Fix Check ---")
    print(f"Jobs needing H1B fix: {len(evaluated_no_h1b)}")
    
    has_jd = 0
    for r in evaluated_no_h1b:
        jd = r.get("Job Description") or ""
        if len(jd.strip()) > 100:
            has_jd += 1
            
    print(f"Jobs with full JD in Sheet: {has_jd}")
    
    # Check cache for the rest
    if has_jd < len(evaluated_no_h1b):
        cache = client._load_jd_cache()
        cached_count = 0
        for r in evaluated_no_h1b:
            url = r.get("Job Link")
            if url and client.get_jd_for_url(url):
                cached_count += 1
        print(f"Jobs with JD in local cache: {cached_count}")

if __name__ == "__main__":
    check_jd_availability()
