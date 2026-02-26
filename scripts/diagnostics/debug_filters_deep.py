from jobspy import scrape_jobs
import pandas as pd
import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.core.job_filters import passes_sourcing_filter

def debug_filters():
    queries = ["Product Manager", "Business Analyst"]
    location = "United States"
    print(f"\n--- Deep Debug: JobSpy Filters ---")
    
    for query in queries:
        try:
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed", "glassdoor", "google", "zip_recruiter"],
                search_term=query,
                location=location,
                results_wanted=20,
                hours_old=72,
                country_indeed="USA",
            )
            
            if jobs.empty:
                print(f"No results for {query}")
                continue

            passed_count = 0
            fail_reasons = {}

            for _, row in jobs.iterrows():
                job = {
                    "title": row.get("title"),
                    "company": row.get("company"),
                    "url": row.get("job_url"),
                    "location": row.get("location"),
                    "description": row.get("description", "")
                }
                
                passed, reason = passes_sourcing_filter(job)
                if passed:
                    passed_count += 1
                else:
                    fail_reasons[reason] = fail_reasons.get(reason, 0) + 1
                    if fail_reasons[reason] <= 2: # Print sample for each reason
                        print(f"  Sample Rejection ({reason}): {job['title']} @ {job['location']}")

            print(f"\nResults for '{query}':")
            print(f"  Total: {len(jobs)}")
            print(f"  Passed: {passed_count}")
            print(f"  Rejected: {len(jobs) - passed_count}")
            for reason, count in fail_reasons.items():
                print(f"    - {reason}: {count}")
                
        except Exception as e:
            print(f"Error for {query}: {e}")

if __name__ == "__main__":
    debug_filters()
