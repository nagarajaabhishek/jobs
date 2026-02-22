import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from jobspy import scrape_jobs
from src.core.google_sheets_client import GoogleSheetsClient
from src.core.config import get_sourcing_config
from src.core.job_filters import passes_sourcing_filter
from src.scrapers.community_scraper import CommunityScraper
from src.scrapers.jobright_scraper import JobrightScraper
from src.scrapers.arbeitnow_scraper import ArbeitnowScraper
from src.scrapers.ats_scraper import ATS_Scraper
from src.scrapers.remotive_scraper import RemotiveScraper
from src.scrapers.remoteok_scraper import RemoteOKScraper
from src.scrapers.ashby_scraper import AshbyScraper

import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)


class SourcingAgent:
    def __init__(self, sheets_client):
        self.sheets_client = sheets_client
        cfg = get_sourcing_config()
        ats = cfg.get("ats_boards") or {}
        self.community_scraper = CommunityScraper()
        self.jobright_scraper = JobrightScraper()
        self.arbeitnow_scraper = ArbeitnowScraper()
        self.ats_scraper = ATS_Scraper(
            greenhouse_boards=ats.get("greenhouse"),
            lever_boards=ats.get("lever"),
        )
        self.remotive_scraper = RemotiveScraper(limit=100)
        self.remoteok_scraper = RemoteOKScraper(limit=80)
        self.ashby_scraper = AshbyScraper(boards=ats.get("ashby"))

    def scrape_community_sources_once(self, queries=None):
        """
        Run Community, Jobright, Arbeitnow, ATS, Remotive, RemoteOK, Ashby once per pipeline.
        """
        queries = queries or ["Product Manager", "Project Manager", "Business Analyst"]
        all_jobs = []
        print("\n--- Scraping Community & API Sources (once) ---")
        sources = [
            ("Community", self.community_scraper, False),
            ("Jobright", self.jobright_scraper, False),
            ("Arbeitnow", self.arbeitnow_scraper, True),
            ("ATS", self.ats_scraper, False),
            ("Remotive", self.remotive_scraper, False),
            ("RemoteOK", self.remoteok_scraper, False),
            ("Ashby", self.ashby_scraper, False),
        ]
        for name, scraper, use_queries in sources:
            try:
                print(f"Scraping {name}...")
                if use_queries:
                    jobs = scraper.scrape(queries=queries)
                elif name in ("Remotive", "RemoteOK"):
                    jobs = scraper.scrape()
                else:
                    jobs = scraper.scrape_all()
                if jobs:
                    print(f"Found {len(jobs)} jobs from {name}. Filtering and saving...")
                    self.normalize_and_save(jobs)
                    all_jobs.extend(jobs)
            except Exception as e:
                print(f"Error scraping {name}: {e}")
        return all_jobs

    def _jobspy_one(self, query, location, results_wanted):
        """Run JobSpy for one (query, location). Returns list of job dicts (empty on error)."""
        try:
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed", "glassdoor", "google", "zip_recruiter"],
                search_term=query,
                location=location,
                results_wanted=results_wanted,
                hours_old=72,
                country_indeed="USA",
            )
            if jobs.empty:
                return []
            jobs_dict = jobs.to_dict("records")
            return [
                {
                    "title": jd.get("title"),
                    "company": jd.get("company"),
                    "url": jd.get("job_url"),
                    "location": jd.get("location"),
                    "source": jd.get("site"),
                    "description": jd.get("description", ""),
                }
                for jd in jobs_dict
            ]
        except Exception as e:
            logging.warning(f"JobSpy failed for '{query}' in '{location}': {e}")
            return []

    def scrape_jobspy_parallel(self, queries, locations, results_wanted=50, max_workers=4):
        """
        Run JobSpy for all (query, location) pairs in parallel. Saves each batch on the main thread.
        """
        tasks = [(q, loc) for q in queries for loc in locations]
        total = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(self._jobspy_one, q, loc, results_wanted): (q, loc)
                for q, loc in tasks
            }
            for future in as_completed(future_to_task):
                q, loc = future_to_task[future]
                try:
                    batch = future.result()
                    if batch:
                        print(f"JobSpy '{q}' in '{loc}': {len(batch)} jobs → saving...")
                        self.normalize_and_save(batch)
                        total += len(batch)
                except Exception as e:
                    logging.warning(f"Task ({q}, {loc}) failed: {e}")
        print(f"JobSpy parallel run complete. Total jobs saved from JobSpy: {total}.")
        return total

    def scrape(self, queries=["Product", "Analytics", "Operations", "Strategy", "Data", "Manager", "Scrum"], locations=["Remote", "United States", "Dubai"], results_wanted=50, include_community_sources=True):
        """
        Scrapes jobs from JobSpy and optionally from Community/Jobright/Arbeitnow/ATS.
        Set include_community_sources=False when calling in a loop; run scrape_community_sources_once() once before the loop instead.
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
                        batch = []
                        for jd in jobs_dict:
                            # Standardize job dict keys for the filter matching
                            batch.append({
                                'title': jd.get('title'),
                                'company': jd.get('company'),
                                'url': jd.get('job_url'),
                                'location': jd.get('location'),
                                'source': jd.get('site'),
                                'description': jd.get('description', '')
                            })
                        
                        # NEW: Checkpoint Save for JobSpy batch
                        print(f"Found {len(batch)} jobs for {query}. Filtering and saving checkpoint...")
                        self.normalize_and_save(batch)
                        
                    else:
                        print(f"No jobs found for {query} via JobSpy.")
                        
                except Exception as e:
                    print(f"Error scraping JobSpy for {query}: {e}")

        # 2. Scrape additional sources only when requested (avoid running 24x per pipeline)
        if include_community_sources:
            community_jobs = self.scrape_community_sources_once(queries=queries)
            all_jobs.extend(community_jobs)

        return all_jobs


    def filter_jobs(self, jobs):
        """
        Filters jobs based on user criteria before they are saved to Google Sheets.
        Uses shared rules from src.core.job_filters.
        """
        filtered_jobs = []
        for job in jobs:
            passed, reason = passes_sourcing_filter(job)
            if not passed:
                logging.info(f"Skipped: {reason} [{job.get('title', '')}]")
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
    # Full Sweep Sourcing
    client = GoogleSheetsClient()
    agent = SourcingAgent(client)
    
    # 1. Primary Roles in Major Markets & Remote
    queries = [
        "Product Manager", "Project Manager", "Program Manager", 
        "Business Analyst", "Product Owner", "Scrum Master",
        "Strategy Operations", "GTM Manager"
    ]
    locations = ["Remote", "United States", "Dubai"]

    
    print(f"\n🚀 Starting Comprehensive Sourcing Sweep...")
    print(f"Platforms: LinkedIn, Google Jobs, Glassdoor, ZipRecruiter, Indeed")
    print(f"Queries: {len(queries)} | Locations: {len(locations)}")
    
    raw_jobs = agent.scrape(queries=queries, locations=locations, results_wanted=50)
    
    print(f"\n✅ Scrape Complete. Total raw jobs found: {len(raw_jobs)}")
    
    try:
        agent.normalize_and_save(raw_jobs)
    except Exception as e:
        print(f"\n❌ Could not save to Google Sheets: {e}")

