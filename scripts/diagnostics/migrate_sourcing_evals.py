import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.google_sheets_client import GoogleSheetsClient
from src.agents.evaluate_jobs import JobEvaluator

def migrate_evals():
    client = GoogleSheetsClient()
    evaluator = JobEvaluator()
    
    # Use the evaluator's parsing logic
    rows = client.get_all_jobs()
    
    updates = []
    ws = client.sheet # Today's sheet
    
    print(f"\n--- Migrating Sourcing Tags for {ws.title} ---")
    
    count = 0
    for i, row in enumerate(rows):
        status = row.get("Status")
        tags = str(row.get("Sourcing Tags", "")).strip()
        
        # If it's NEW and has evaluation-like tags
        if status == "NEW" and "**Match Type**" in tags:
            # Row index is i + 2 (1-based + header)
            row_idx = i + 2
            
            # Parse using evaluator logic
            parsed = evaluator.parse_evaluation(tags)
            match_type, rec, h1b, loc, missing, reason, salary, tech, score = parsed
            
            # Fallback for score if missing
            if score == 0:
                jd_link = row.get("Job Link") or ""
                jd_text = client.get_jd_for_url(jd_link) or ""
                score = evaluator._compute_fallback_score(jd_text, row.get("Location") or "")
            
            # Use shared verdict mapping
            from src.agents.evaluate_jobs import score_to_verdict
            match_type = score_to_verdict(score)
            
            updates.append((row_idx, match_type, rec, h1b, loc, missing, score, reason))
            count += 1
            if count <= 5:
                print(f"  Parsed {row.get('Role Title')}: {match_type} ({score})")

    if updates:
        print(f"\nReady to update {len(updates)} jobs.")
        client.update_evaluated_jobs(ws, updates)
        print("Migration complete. Sorting sheet...")
        client.sort_daily_jobs()
    else:
        print("No jobs found with processable sourcing tags.")

if __name__ == "__main__":
    migrate_evals()
