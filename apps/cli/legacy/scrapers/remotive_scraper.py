"""
Remotive remote jobs API. Free; use sparingly (max ~4 requests/day).
Must credit Remotive and link back. Jobs delayed 24h.
"""
import requests

REMOTIVE_API = "https://remotive.com/api/remote-jobs"


class RemotiveScraper:
    def __init__(self, limit=100):
        self.limit = limit

    def scrape(self):
        all_jobs = []
        try:
            response = requests.get(REMOTIVE_API, params={"limit": self.limit}, timeout=15)
            response.raise_for_status()
            data = response.json()
            jobs = data.get("jobs", [])
            for job in jobs:
                loc = job.get("candidate_required_location") or "Remote"
                all_jobs.append({
                    "title": job.get("title"),
                    "company": job.get("company_name"),
                    "location": loc,
                    "url": job.get("url", ""),
                    "source": "Remotive",
                    "description": (job.get("description") or "")[:8000],
                })
            print(f"Remotive: found {len(all_jobs)} remote jobs.")
        except Exception as e:
            print(f"Remotive API error: {e}")
        return all_jobs
