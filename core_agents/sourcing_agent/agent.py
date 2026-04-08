import os
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from jobspy import scrape_jobs
from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient
from apps.cli.legacy.core.config import get_sourcing_config, get_evaluation_config
from apps.cli.legacy.core.job_filters import (
    filter_sourcing_jobs,
    print_sourcing_filter_summary,
)
from apps.cli.legacy.scrapers.community_scraper import CommunityScraper
from apps.cli.legacy.scrapers.jobright_scraper import JobrightScraper
from apps.cli.legacy.scrapers.arbeitnow_scraper import ArbeitnowScraper
from apps.cli.legacy.scrapers.ats_scraper import ATS_Scraper
from apps.cli.legacy.scrapers.remotive_scraper import RemotiveScraper
from apps.cli.legacy.scrapers.remoteok_scraper import RemoteOKScraper
from apps.cli.legacy.scrapers.ashby_scraper import AshbyScraper
from apps.cli.legacy.scrapers.dice_scraper import DiceScraper
from apps.cli.legacy.core.llm_router import LLMRouter

import pandas as pd # type: ignore
import json
import os
import requests # type: ignore
from bs4 import BeautifulSoup # type: ignore
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

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
        self.dice_scraper = DiceScraper()
        self.llm = LLMRouter()
        self._last_sourcing_filter_stats: dict[str, int] = {}
        
        # Load Phase 1 Dense Matrix for Phase 2 Sniffing
        self.dense_matrix = {}
        matrix_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "dense_master_matrix.json")
        try:
            if os.path.exists(matrix_path):
                with open(matrix_path, "r") as f:
                    self.dense_matrix = json.load(f)
        except Exception as e:
            logging.warning(f"Could not load dense matrix: {e}")

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
            ("Dice", self.dice_scraper, True),
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

    def _jobspy_site_names(self):
        cfg = get_sourcing_config()
        sites = cfg.get("jobspy_sites")
        if sites and isinstance(sites, list):
            return sites
        return ["linkedin", "indeed", "google", "zip_recruiter"]

    def _jobspy_one(self, query, location, results_wanted):
        """Run JobSpy for one (query, location). Returns list of job dicts (empty on error)."""
        try:
            jobs = scrape_jobs(
                site_name=self._jobspy_site_names(),
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
                    "title": str(jd.get("title") or ""),
                    "company": str(jd.get("company") or ""),
                    "url": str(jd.get("job_url") or ""),
                    "location": str(jd.get("location") or ""),
                    "source": str(jd.get("site") or ""),
                    "description": str(jd.get("description") or ""),
                }
                for jd in jobs_dict
            ]
        except Exception as e:
            logging.warning(f"JobSpy failed for '{query}' in '{location}': {e}")
            return []

    def scrape_jobspy_parallel(self, queries, locations, max_workers=4, use_ai_filter=False):
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
                        self.normalize_and_save(batch, use_ai_filter=use_ai_filter)
                        total += len(batch)
                except Exception as e:
                    logging.warning(f"Task ({q}, {loc}) failed: {e}")
        print(f"JobSpy parallel run complete. Total jobs processed from JobSpy: {total}.")
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
                        site_name=self._jobspy_site_names(),
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
        
    def _fetch_jd_manually(self, url: str) -> tuple[str, bool, str]:
        """
        Secondary JD Resolution: Fallback used when JobSpy or APIs fail to return a JD.
        Attempts to scrape the main text content of the page directly.
        Uses a tiered approach:
        1. Fast Scrape (Requests/BS4)
        2. Deep Scrape (Playwright) for JS-heavy sites
        """
        if not url or "google.com" in url:
            return "", False, "skipped"
        
        # 1. Fast Scrape
        jd, ok, method = self._fetch_jd_static(url)
        if ok and len(jd) > 300:
            return jd, True, method
            
        # 2. Deep Scrape (Playwright Fallback)
        if sync_playwright:
            print(f"    🔄 Fast Scrape too short ({len(jd)} chars). Trying Playwright...")
            jd_deep, ok2, method2 = self._fetch_jd_playwright(url)
            if ok2 and len(jd_deep) > len(jd):
                return jd_deep, True, method2
        
        return jd, False, method or "static_unverified"

    def _fetch_jd_static(self, url: str) -> tuple[str, bool, str]:
        """Fast, static HTML extraction. Selector-only (no full-page fallback)."""
        print(f"    🔍 Static JD Fetch: {url}...")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            
            soup = BeautifulSoup(r.text, "html.parser")
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
                
            # Common ATS selectors
            selectors = [
                ".job-description", "#job-description", ".description", 
                ".posting-description", "#content", "main", "[data-automation-id='job-posting-description']",
                ".jd-content", ".careers-job-description"
            ]
            
            for selector in selectors:
                found = soup.select_one(selector)
                if found:
                    content = found.get_text(separator="\n").strip()
                    if len(content) > 100:
                        print(f"    ✅ Static fetch successful ({len(content)} chars).")
                        return self._clean_text(content), True, f"static:{selector}"
            # Hard rule: if selector not found, JD is unverified and cannot be evaluated.
            return "", False, "static:selector_miss"
        except Exception as e:
            print(f"    ⚠ Static fetch failed: {e}")
            return "", False, "static:error"

    def _fetch_jd_playwright(self, url: str) -> tuple[str, bool, str]:
        """Deep scrape using headless browser for JS-heavy sites. Selector-only (no full-page fallback)."""
        if not sync_playwright:
            return "", False, "playwright:unavailable"
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=20000)
                
                # Give it a tiny bit extra for late-loading React components
                page.wait_for_timeout(2000)
                
                # Check same selectors in browser context
                content = ""
                selectors = [
                    ".job-description", "#job-description", ".description", 
                    ".posting-description", "#content", "main", "[data-automation-id='job-posting-description']",
                    ".jd-content", ".careers-job-description"
                ]
                
                for selector in selectors:
                    try:
                        element = page.query_selector(selector)
                        if element:
                            text = element.inner_text()
                            if len(text) > 100:
                                content = text
                                break
                    except:
                        continue
                
                browser.close()
                if len(content) > 100:
                    print(f"    ✅ Playwright fetch successful ({len(content)} chars).")
                    return self._clean_text(content), True, "playwright:selector"
        except Exception as e:
            print(f"    ⚠ Playwright fetch failed: {e}")
        return "", False, "playwright:error"

    def _clean_text(self, text: str) -> str:
        """Helper to cleanup scraped text."""
        import re
        # Remove excessive whitespace/newlines
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()


    def filter_jobs(self, jobs):
        """
        Filters jobs based on user criteria before they are saved to Google Sheets.
        """
        filtered_jobs, stats = filter_sourcing_jobs(jobs, log_each=False)
        self._last_sourcing_filter_stats = stats
        print(f"Filtered down to {len(filtered_jobs)} jobs from {len(jobs)}.")
        return filtered_jobs

    def ai_sniff_relevance(self, job):
        """
        AI pre-filter: uses a fast/cheap LLM via OpenRouter to 'sniff' if a job violates
        the hard constraints from our Phase 1 Dense Matrix (YOE, Clearance, Role match).
        Returns (True, "Reason") or (False, "Reason").
        """
        title = job.get("title", "")
        desc = job.get("description", "")[:800] # Slightly larger snippet for YOE search
        
        # Extract traits from Phase 1 matrix (default safe fallback if missing)
        traits = self.dense_matrix.get("global_traits", {})
        yoe = traits.get("years_of_experience", 3)
        clearance = traits.get("clearance", "None")
        
        system_prompt = f"""
        You are a recruitment classifier. Analyze the Job Title and Snippet against these HARD CONSTRAINTS:
        1. User has {yoe} Years of Experience (YOE). If the job strictly demands significantly more (e.g., 5+, 7+, or Senior/Lead roles), reject it.
        2. User Security Clearance: {clearance}. If the job strictly requires an active clearance (Secret, Top Secret, TS/SCI), reject it.
        3. Role Relevance: Is this a Product Manager, Project Manager, Program Manager, Business Analyst, Product Owner, Scrum Master, or GTM/Strategy Operations role? If no, reject it.
        
        Answer ONLY YES or NO.
        """
        user_prompt = f"Title: {title}\nSnippet: {desc}"
        
        # We can force a cheap model for this (Gemini 2.5 Flash-Lite)
        eval_cfg = get_evaluation_config()
        sourcing_model = eval_cfg.get("sourcing_model", "gemini-2.5-flash-lite")
        
        text, engine = self.llm.generate_content(system_prompt, user_prompt, model=sourcing_model)
        
        if engine == "FAILED":
            return True, "LLM failed - allowing through"
            
        result = text.strip().upper()
        if "YES" in result:
            return True, f"AI confirmed relevance ({engine} - {sourcing_model})"
        return False, f"AI rejected: Sniffer Mismatch ({engine} - {sourcing_model})"

    def normalize_and_save(self, raw_jobs, use_ai_filter=False):
        """
        Normalizes job data, applies filters, and saves to Google Sheets.
        """
        raw_n = len(raw_jobs or [])
        # 1. Static Rule Filter
        filtered_raw_jobs = self.filter_jobs(raw_jobs)
        static_stats = dict(self._last_sourcing_filter_stats)
        after_static_count = len(filtered_raw_jobs)
        
        # 2. AI Pre-filter (Optional)
        ai_rejected = 0
        if use_ai_filter and filtered_raw_jobs:
            print(f"--- AI Sniffing {len(filtered_raw_jobs)} jobs for relevance ---")
            ai_passed = []
            for job in filtered_raw_jobs:
                passed, reason = self.ai_sniff_relevance(job)
                if passed:
                    ai_passed.append(job)
                else:
                    ai_rejected += 1
                    logging.info("AI Filtered: %s [%s]", reason, job.get("title", ""))
            print(f"AI Sniffing complete. {len(ai_passed)} passed.")
            filtered_raw_jobs = ai_passed

        # 3. Final Normalize & Tagging
        clean_jobs = []
        for job in filtered_raw_jobs:
            if not job:
                continue
            # Optional: Add tags to the description/metadata if needed, 
            # Or just store them in a way the evaluator can see.
            # For now, we'll just log them or add to a side-car field.
            tags = self.tag_job(job)
            
            # JD resolution (hard-gated): selector-only verification.
            desc = job.get("description", "")
            jd_verified = bool(desc and isinstance(desc, str) and len(desc) >= 200 and desc.lower() != "none")
            jd_fetch_method = "source"
            jd_fetch_reason = ""
            if (not jd_verified) and job.get("url"):
                manual_desc, ok, method = self._fetch_jd_manually(job.get("url"))
                if ok and manual_desc:
                    desc = manual_desc
                    jd_verified = True
                    jd_fetch_method = method
                else:
                    desc = ""
                    jd_verified = False
                    jd_fetch_method = method
                    jd_fetch_reason = "selector_only_jd_not_found"
            
            clean_job = {
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "url": job.get("url") or job.get("job_url", ""),
                "location": job.get("location", ""),
                "source": job.get("source") or job.get("site", "Unknown"),
                "description": desc,
                "tags": tags,  # NEW field for Sheets
                "jd_verified": jd_verified,
                "jd_fetch_method": jd_fetch_method,
                "jd_fetch_reason": jd_fetch_reason,
            }
            clean_jobs.append(clean_job)

        print_sourcing_filter_summary(
            static_stats,
            raw_count=raw_n,
            after_static=after_static_count,
            ai_rejected=ai_rejected,
            saved_count=len(clean_jobs),
        )
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

