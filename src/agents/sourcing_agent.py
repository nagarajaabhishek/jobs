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
from src.core.llm_router import LLMRouter

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
        self.llm = LLMRouter()

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

    def scrape_jobspy_parallel(self, queries, locations, max_workers=4):
        """
        Run JobSpy for all (query, location) pairs in parallel.
        locations can be a list or a dict {location: results_wanted}.
        """
        if isinstance(locations, list):
            # Fallback for old list format
            tasks = [(q, loc, 50) for q in queries for loc in locations]
        else:
            # New dict format: {location: target}
            tasks = [(q, loc, target) for q in queries for loc, target in locations.items()]

        total = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(self._jobspy_one, q, loc, target): (q, loc)
                for q, loc, target in tasks
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

    def expand_queries(self, base_roles=["Product Manager", "Business Analyst", "Scrum Master"]):
        """
        AI Query Expansion: uses a reasoning model to find related job titles 
        that might be missed by static keyword searches.
        """
        print(f"--- AI Query Expansion for: {base_roles} ---")
        system_prompt = """
        You are a recruitment strategist. Given a list of core job roles, provide 10-15 short, 
        effective search phrases used in LinkedIn/Indeed job titles for these roles.
        Focus on variations, seniority levels, and Niche titles.
        
        Output format: A comma-separated list of titles ONLY. No numbering or extra text.
        """
        user_prompt = f"Core roles: {base_roles}"
        
        text, engine = self.llm.generate_content(system_prompt, user_prompt)
        if engine == "FAILED":
            return base_roles
            
        expanded = [t.strip() for t in text.split(",") if t.strip()]
        print(f"Expanded queries ({engine}): {expanded}")
        return expanded

    def tag_job(self, job):
        """
        Lightweight Tagging: extracts metadata (Work style, Seniority, Industry) 
        from the job title and snippet.
        """
        title = job.get("title", "")
        desc = job.get("description", "")[:400]
        
        system_prompt = """
        Analyze the job title and snippet. Extract:
        1. Work Style: Remote, Hybrid, or Onsite
        2. Seniority: Intern, Junior, Mid, Senior, Lead, or Director
        3. Industry: Tech, Finance, Health, Retail, or Other
        
        Output EXACTLY: Style: [Style] | Seniority: [Seniority] | Industry: [Industry]
        """
        user_prompt = f"Job: {title}\nSnippet: {desc}"
        
        text, engine = self.llm.generate_content(system_prompt, user_prompt)
        if engine == "FAILED":
            return "Tags: Unknown"
        return text.strip()

    def scrape(self, queries=["Product", "Analytics", "Operations", "Strategy", "Data", "Manager", "Scrum"], locations=None, results_wanted=50, include_community_sources=True, expand_ai_queries=False):
        """
        Scrapes jobs from JobSpy and optionally from Community/Jobright/Arbeitnow/ATS.
        """
        if expand_ai_queries:
            queries = self.expand_queries(queries)

        if locations is None:
            locations = {"Remote": 50, "United States": 50, "Dubai": 50}
            
        all_jobs = []

        # 1. Scrape with JobSpy
        for query in queries:
            if isinstance(locations, dict):
                loc_items = locations.items()
            else:
                loc_items = [(loc, results_wanted) for loc in locations]

            for location, target in loc_items:
                print(f"Scraping JobSpy for '{query}' in '{location}' (target: {target})...")
                try:
                    jobs = scrape_jobs(
                        site_name=["linkedin", "indeed", "glassdoor", "google", "zip_recruiter"],
                        search_term=query,
                        location=location,
                        results_wanted=target,
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

    def ai_sniff_relevance(self, job):
        """
        Optional AI pre-filter: uses a fast/cheap LLM via OpenRouter to 'sniff' if a job is actually 
        within our target role families (PM, PO, BA, SM, GTM).
        Returns (True, "Role Matched") or (False, Reason).
        """
        title = job.get("title", "")
        desc = job.get("description", "")[:500] # Snippet for speed/cost
        
        system_prompt = """
        You are a recruitment classifier. Analyze the Job Title and Snippet.
        Is this a role for a Product Manager, Project Manager, Program Manager, Business Analyst, 
        Product Owner, Scrum Master, or GTM/Strategy Operations?
        
        Answer ONLY: YES or NO.
        """
        user_prompt = f"Title: {title}\nSnippet: {desc}"
        
        # We can force a cheap model for this in the future, for now uses router default
        text, engine = self.llm.generate_content(system_prompt, user_prompt)
        
        if engine == "FAILED":
            return True, "LLM failed - allowing through"
            
        result = text.strip().upper()
        if "YES" in result:
            return True, f"AI confirmed relevance ({engine})"
        return False, f"AI sniffed mismatch ({engine})"

    def normalize_and_save(self, raw_jobs, use_ai_filter=False):
        """
        Normalizes job data, applies filters, and saves to Google Sheets.
        """
        # 1. Static Rule Filter
        filtered_raw_jobs = self.filter_jobs(raw_jobs)
        
        # 2. AI Pre-filter (Optional)
        if use_ai_filter and filtered_raw_jobs:
            print(f"--- AI Sniffing {len(filtered_raw_jobs)} jobs for relevance ---")
            ai_passed = []
            for job in filtered_raw_jobs:
                passed, reason = self.ai_sniff_relevance(job)
                if passed:
                    ai_passed.append(job)
                else:
                    logging.info(f"AI Filtered: {reason} [{job.get('title', '')}]")
            print(f"AI Sniffing complete. {len(ai_passed)} passed.")
            filtered_raw_jobs = ai_passed

        # 3. Final Normalize & Tagging
        clean_jobs = []
        for job in filtered_raw_jobs:
            # Optional: Add tags to the description/metadata if needed, 
            # Or just store them in a way the evaluator can see.
            # For now, we'll just log them or add to a side-car field.
            tags = self.tag_job(job)
            
            clean_job = {
                "title": job.get("title"),
                "company": job.get("company"),
                "url": job.get("url") or job.get("job_url"),
                "location": job.get("location"),
                "source": job.get("source") or job.get("site"),
                "description": job.get("description", ""),
                "tags": tags # NEW field for Sheets
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

