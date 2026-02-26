from jobspy import scrape_jobs
import pandas as pd

def debug_jobspy():
    query = "Product Manager"
    location = "United States"
    print(f"\n--- Debugging JobSpy: '{query}' in '{location}' ---")
    
    try:
        jobs = scrape_jobs(
            site_name=["linkedin", "indeed", "glassdoor", "google", "zip_recruiter"],
            search_term=query,
            location=location,
            results_wanted=10,
            hours_old=72,
            country_indeed="USA",
        )
        
        if jobs.empty:
            print("JobSpy returned NO jobs.")
            return

        print(f"Found {len(jobs)} raw jobs. Inspecting first 5:")
        for i, row in jobs.head(5).iterrows():
            print(f"\nJob {i+1}:")
            print(f"  Title: {row.get('title')}")
            print(f"  Location: {row.get('location')}")
            print(f"  Site: {row.get('site')}")
            
    except Exception as e:
        print(f"JobSpy Error: {e}")

if __name__ == "__main__":
    debug_jobspy()
