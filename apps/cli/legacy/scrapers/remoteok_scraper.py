"""
Remote OK remote jobs. Free JSON API at remoteok.com/api.
Returns a large array; we take the first N and normalize.
"""
import requests

REMOTEOK_API = "https://remoteok.com/api"


class RemoteOKScraper:
    def __init__(self, limit=80):
        self.limit = limit

    def scrape(self):
        all_jobs = []
        try:
            # API returns array; first element can be metadata
            response = requests.get(REMOTEOK_API, headers={"User-Agent": "JobAutomation/1.0"}, timeout=30)
            response.raise_for_status()
            raw = response.json()
            if not isinstance(raw, list):
                return all_jobs
            count = 0
            for item in raw:
                if count >= self.limit:
                    break
                if not isinstance(item, dict):
                    continue
                # Skip metadata row (often has 'id' as string or different shape)
                job_id = item.get("id")
                if job_id is None or (isinstance(job_id, str) and not job_id.isdigit()):
                    continue
                slug = item.get("slug") or str(job_id)
                url = item.get("url") or f"https://remoteok.com/l/{slug}"
                title = item.get("position") or item.get("title") or ""
                company = item.get("company") or ""
                if not title and not company:
                    continue
                location = item.get("location") or "Remote"
                desc = item.get("description") or ""
                if isinstance(desc, str) and len(desc) > 8000:
                    desc = desc[:8000]
                all_jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": url,
                    "source": "RemoteOK",
                    "description": desc,
                })
                count += 1
            print(f"RemoteOK: found {len(all_jobs)} remote jobs.")
        except Exception as e:
            print(f"RemoteOK API error: {e}")
        return all_jobs
