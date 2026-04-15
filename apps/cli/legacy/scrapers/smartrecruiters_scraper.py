"""
SmartRecruiters public postings API scraper.
Endpoint: GET https://api.smartrecruiters.com/v1/companies/{company}/postings
"""

import requests


class SmartRecruitersScraper:
    def __init__(self, companies=None, page_size=100):
        self.companies = [str(x).strip() for x in (companies or []) if str(x).strip()]
        self.page_size = max(1, min(int(page_size), 100))

    def scrape_company(self, company):
        jobs = []
        offset = 0
        while True:
            url = f"https://api.smartrecruiters.com/v1/companies/{company}/postings"
            params = {"limit": self.page_size, "offset": offset}
            try:
                response = requests.get(url, params=params, timeout=20)
                if response.status_code == 404:
                    break
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                print(f"SmartRecruiters ({company}) error: {e}")
                break

            items = data.get("content") or []
            if not isinstance(items, list) or not items:
                break

            for item in items:
                if not isinstance(item, dict):
                    continue
                title = str(item.get("name") or "").strip()
                posting_id = str(item.get("id") or "").strip()
                if not title or not posting_id:
                    continue
                city = str(item.get("location", {}).get("city") or "").strip()
                region = str(item.get("location", {}).get("region") or "").strip()
                country = str(item.get("location", {}).get("country") or "").strip()
                location = ", ".join([x for x in (city, region, country) if x]) or "Unknown"
                jobs.append(
                    {
                        "title": title,
                        "company": str(item.get("company", {}).get("name") or company).strip(),
                        "location": location,
                        "url": f"https://jobs.smartrecruiters.com/{company}/{posting_id}",
                        "source": "ATS_SmartRecruiters",
                        "description": str(item.get("jobAd", {}).get("sections", {}) or "")[:8000],
                    }
                )

            total_found = data.get("totalFound")
            offset += len(items)
            if (isinstance(total_found, int) and offset >= total_found) or len(items) < self.page_size:
                break

        if jobs:
            print(f"SmartRecruiters ({company}): {len(jobs)} jobs.")
        return jobs

    def scrape_all(self):
        all_jobs = []
        for company in self.companies:
            all_jobs.extend(self.scrape_company(company))
        return all_jobs
