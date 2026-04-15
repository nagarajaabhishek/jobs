"""
Recruitee careers API scraper.
Endpoint: GET https://{company}.recruitee.com/api/offers/
"""

import requests


class RecruiteeScraper:
    def __init__(self, companies=None):
        self.companies = [str(x).strip() for x in (companies or []) if str(x).strip()]

    def scrape_company(self, company):
        jobs = []
        url = f"https://{company}.recruitee.com/api/offers/"
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Recruitee ({company}) error: {e}")
            return []

        offers = data.get("offers") or []
        for item in offers:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            careers_url = str(item.get("careers_url") or item.get("url") or "").strip()
            if not title or not careers_url:
                continue
            city = str(item.get("location") or "").strip()
            country = str(item.get("country") or "").strip()
            location = ", ".join([x for x in (city, country) if x]) or "Unknown"
            jobs.append(
                {
                    "title": title,
                    "company": str(item.get("company_name") or company).strip(),
                    "location": location,
                    "url": careers_url,
                    "source": "ATS_Recruitee",
                    "description": str(item.get("description") or "")[:8000],
                }
            )

        if jobs:
            print(f"Recruitee ({company}): {len(jobs)} jobs.")
        return jobs

    def scrape_all(self):
        all_jobs = []
        for company in self.companies:
            all_jobs.extend(self.scrape_company(company))
        return all_jobs
