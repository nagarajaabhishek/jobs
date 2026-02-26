import sys
import os
import re
import requests
from bs4 import BeautifulSoup

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.google_sheets_client import GoogleSheetsClient
from src.core.llm_router import LLMRouter

def fetch_jd_minimal(url):
    """Simple requests-based scraper for job pages to get JD text for H1B analysis."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Extract text from common JD containers or just the whole body
            text = soup.get_text(separator=' ', strip=True)
            return text[:10000] # Limit for LLM
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
    return ""

def check_sponsorship_and_loc(llm, jd_text):
    """Specifically ask the LLM about sponsorship and location constraints."""
    system_prompt = "You are a recruitment specialist. Extract ONLY specific data from the Job Description."
    user_prompt = f"JD:\n{jd_text}\n\nTasks:\n1. H1B: Does it mention sponsorship? (Yes/No/Explicitly No/Not Mentioned)\n2. Location: Is it remote? If so, are there state/country restrictions? (e.g. Remote - USA ONLY)\n\nAnswer EXACTLY in this format:\nH1B: [Answer]\nLOC: [Answer]"
    
    res, model = llm.generate_content(system_prompt, user_prompt)
    return res.strip()

def fix_h1b():
    client = GoogleSheetsClient()
    llm = LLMRouter()
    rows = client.get_all_jobs()
    ws = client.sheet
    
    # Target top matches with unknown H1B
    targets = [
        (i+2, r) for i, r in enumerate(rows)
        if r.get("Status") == "EVALUATED" 
        and (str(r.get("H1B Sponsorship", "")).lower() in ["unknown", "—", ""] or str(r.get("Location Verification", "")).lower() in ["unknown", "—", ""])
        and str(r.get("Match Type", "")).lower().replace("*", "") in ["🔥 auto-apply", "✅ strong match", "for sure"]
    ]
    
    print(f"\n--- Enriching {len(targets)} Top Matches (H1B + Loc) ---")
    
    updates = []
    for row_idx, r in targets:
        url = r.get("Job Link")
        role = r.get("Role Title")
        print(f"Processing: {role}...")
        
        jd = fetch_jd_minimal(url)
        if not jd:
            print("  Could not fetch JD.")
            continue
            
        raw_res = check_sponsorship_and_loc(llm, jd)
        print(f"  Raw Result:\n{raw_res}")
        
        # Parse simple lines
        h1b_status = "Not Mentioned"
        loc_status = "Confirmed"
        
        for line in raw_res.split('\n'):
            if line.upper().startswith("H1B:"):
                h1b_status = line.split(":", 1)[1].strip()
            elif line.upper().startswith("LOC:"):
                loc_status = line.split(":", 1)[1].strip()
        
        updates.append((
            row_idx, 
            r.get("Match Type"), 
            r.get("Recommended Resume"), 
            h1b_status, 
            loc_status, 
            r.get("Missing Skills"), 
            r.get("Apply Score"),
            r.get("Reasoning") # Keep existing reasoning
        ))

    if updates:
        print(f"\nUpdating {len(updates)} jobs...")
        client.update_evaluated_jobs(ws, updates)
    else:
        print("No updates needed or possible.")

if __name__ == "__main__":
    fix_h1b()
