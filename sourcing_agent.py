from jobspy import scrape_jobs
from google_sheets_client import GoogleSheetsClient
from community_scraper import CommunityScraper
from jobright_scraper import JobrightScraper
from arbeitnow_scraper import ArbeitnowScraper
from ats_scraper import ATS_Scraper
import pandas as pd

import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class SourcingAgent:
    def __init__(self, sheets_client):
        self.sheets_client = sheets_client
        self.community_scraper = CommunityScraper()
        self.jobright_scraper = JobrightScraper()
        self.arbeitnow_scraper = ArbeitnowScraper()
        self.ats_scraper = ATS_Scraper()

    def scrape(self, queries=["Product", "Analytics", "Operations", "Strategy", "Data", "Manager", "Scrum"], locations=["Remote", "United States", "Dubai"], results_wanted=50):
        """
        Scrapes jobs from all defined sources.
        """
        all_jobs = []
        
        # 1. Scrape with JobSpy
        for query in queries:
            for location in locations:
                print(f"Scraping JobSpy for '{query}' in '{location}'...")
                try:
                    jobs = scrape_jobs(
                        site_name=["linkedin", "indeed", "glassdoor", "google", "zip_recruiter"],
                        search_term=query,
                        location=location,
                        results_wanted=results_wanted,
                        hours_old=72, # 3 days back
                        country_indeed='USA'
                    )
                    
                    if not jobs.empty:
                        # Convert DataFrame to list of dicts
                        jobs_dict = jobs.to_dict('records')
                        for jd in jobs_dict:
                            # Standardize job dict keys for the filter matching
                            all_jobs.append({
                                'title': jd.get('title'),
                                'company': jd.get('company'),
                                'url': jd.get('job_url'),
                                'location': jd.get('location'),
                                'source': jd.get('site'),
                                'description': jd.get('description', '')
                            })
                        print(f"Found {len(jobs_dict)} jobs for {query} via JobSpy.")
                    else:
                        print(f"No jobs found for {query} via JobSpy.")
                        
                except Exception as e:
                    print(f"Error scraping JobSpy for {query}: {e}")
                    
        # 2. Scrape additional sources
        print("\n--- Scraping Community & API Sources ---")
        try:
            community_jobs = self.community_scraper.scrape_all()
            all_jobs.extend(community_jobs)
            
            jobright_jobs = self.jobright_scraper.scrape_all()
            all_jobs.extend(jobright_jobs)
            
            # For Arbeitnow, pass the specific queries
            arbeitnow_jobs = self.arbeitnow_scraper.scrape(queries=queries)
            all_jobs.extend(arbeitnow_jobs)
            
            ats_jobs = self.ats_scraper.scrape_all()
            all_jobs.extend(ats_jobs)
        except Exception as e:
            print(f"Error scraping additional sources: {e}")
            
        return all_jobs

    def filter_jobs(self, jobs):
        """
        Filters jobs based on user criteria before they are even saved to Google Sheets.
        """
        filtered_jobs = []
        
        # 1. Broadly allow these roles if they match
        title_inclusions = [
            "product", "project", "program", "business analyst", "data analyst", 
            "go-to market", "gtm", "growth", "strategy", "operations analyst", "scrum master"
        ]
        
        # 2. Strict Exclusions (The Bouncer Rules)
        senior_keywords = ["senior", "sr", "sr.", "staff", "principal", "director", "vp", "head of", "lead", "manager ii"]
        clearance_keywords = ["clearance", "ts/sci", "secret clearance", "top secret"]
        unrelated_keywords = [
            "nurse", "registered nurse", "rn", "physician", "driver", "cdl", 
            "warehouse", "mechanic", "cashier", "architect", "software engineer",
            "backend", "frontend", "fullstack", "full stack", "account executive", "recruiter"
        ]
        location_exclusions = [
            "india", "uk", "london", "canada", "australia", "germany", "france", 
            "singapore", "bangalore", "hyderabad", "toronto"
        ]
        
        for job in jobs:
            title = str(job.get('title', '')).lower()
            location = str(job.get('location', '')).lower()
            desc = str(job.get('url', '')).lower() # Fallback

            # A. Check Title Inclusions (Must match at least one broad category)
            has_included_title = any(inc in title for inc in title_inclusions)
            if not has_included_title:
                continue
                
            # B. Check Senior/Lead Exclusions
            import re
            has_senior = False
            for keyword in senior_keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', title):
                    has_senior = True
                    break
            if has_senior:
                continue
                
            # C. Check Clearance Exclusions
            if any(keyword in title or keyword in desc for keyword in clearance_keywords):
                continue
                
            # D. Check Unrelated Field Exclusions
            has_unrelated = False
            for keyword in unrelated_keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', title):
                    has_unrelated = True
                    break
            if has_unrelated:
                continue
                
            # E. Check Location Exclusions
            if any(exc in location for exc in location_exclusions):
                continue
                
            filtered_jobs.append(job)
            
        print(f"Filtered down to {len(filtered_jobs)} jobs from {len(jobs)}.")
        return filtered_jobs

    def normalize_and_save(self, raw_jobs):
        """
        Normalizes job data and saves to Google Sheets.
        """
        # First filter the jobs
        filtered_raw_jobs = self.filter_jobs(raw_jobs)
        
        clean_jobs = []
        for job in filtered_raw_jobs:
            clean_job = {
                'title': job.get('title'),
                'company': job.get('company'),
                'url': job.get('url') or job.get('job_url'), # Handle different scraper formats
                'location': job.get('location'),
                'source': job.get('source') or job.get('site'), # Handle different scraper formats
                'description': job.get('description', '')
            }
            clean_jobs.append(clean_job)
            
        self.sheets_client.add_jobs(clean_jobs)

if __name__ == "__main__":
    # Test script
    client = GoogleSheetsClient()
    agent = SourcingAgent(client)
    
    # Run a small test scrape
    raw_jobs = agent.scrape(queries=["AI Engineer"], locations=["Remote"], results_wanted=5)
    
    print("\n--- Scraped Jobs Summary ---")
    for job in raw_jobs:
        print(f"- {job.get('title')} at {job.get('company')} ({job.get('site')})")
        
    try:
        agent.normalize_and_save(raw_jobs)
    except Exception as e:
        print(f"\nCould not save to Google Sheets: {e}")
