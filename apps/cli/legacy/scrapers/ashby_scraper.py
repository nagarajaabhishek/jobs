"""
Ashby job board API. No auth. Slug = company identifier (e.g. Ashby, Notion, Figma).
https://developers.ashbyhq.com/docs/public-job-posting-api
"""
import requests

ASHBY_BASE = "https://api.ashbyhq.com/posting-api/job-board"


class AshbyScraper:
    def __init__(self, boards=None):
        self.boards = boards or ["ashby", "notion", "figma", "linear", "vercel", "ramp"]

    def scrape_board(self, slug):
        jobs = []
        try:
            url = f"{ASHBY_BASE}/{slug}"
            response = requests.get(url, timeout=15)
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()
            # Ashby returns jobBoard with jobs array
            job_list = data.get("jobs", []) if isinstance(data, dict) else []
            for job in job_list:
                title = job.get("title") if isinstance(job, dict) else None
                if not title:
                    continue
                loc = (job.get("location") or {}).get("name", "Remote") if isinstance(job.get("location"), dict) else (job.get("location") or "Remote")
                app_url = job.get("applicationUrl") or job.get("url") or ""
                desc = job.get("description") or ""
                if isinstance(desc, str) and len(desc) > 8000:
                    desc = desc[:8000]
                jobs.append({
                    "title": title,
                    "company": slug.capitalize(),
                    "location": loc if isinstance(loc, str) else "Remote",
                    "url": app_url,
                    "source": "ATS_Ashby",
                    "description": desc,
                })
        except Exception as e:
            print(f"Ashby board {slug}: {e}")
        return jobs

    def scrape_all(self):
        all_jobs = []
        for slug in self.boards:
            jobs = self.scrape_board(slug)
            if jobs:
                print(f"Ashby ({slug}): {len(jobs)} jobs.")
                all_jobs.extend(jobs)
        return all_jobs
