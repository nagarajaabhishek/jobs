import requests
from bs4 import BeautifulSoup
import re

class CommunityScraper:
    def __init__(self):
        self.sources = {
            "Simplify_SWE_2026": "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/README.md"
        }

    def scrape_simplify(self, url):
        """
        Scrapes a Simplify-style GitHub repository README.
        These READMEs use HTML <table> tags for internships.
        """
        print(f"Fetching community list from {url}...")
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        jobs = []

        # Find all tables in the markdown
        tables = soup.find_all('table')
        
        for table in tables:
            # Check headers to ensure it's a job table
            headers = [th.text.strip().lower() for th in table.find_all('th')]
            if 'company' in headers and 'role' in headers:
                rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')[1:]
                
                current_company = "Unknown"
                
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        # Handle company grouping (↳)
                        company_col = cols[0].text.strip()
                        if company_col and company_col != '↳':
                            current_company = company_col
                        
                        role = cols[1].text.strip()
                        location = cols[2].text.strip()
                        
                        # Extract application link
                        app_col = cols[3]
                        link = ""
                        links = app_col.find_all('a')
                        # Find the actual application link (not the simplify link usually, or handle the first a href)
                        for a in links:
                            href = a.get('href', '')
                            # Prefer direct application links or at least grab the first valid one
                            if 'simplify.jobs/p/' not in href and href:
                                link = href
                                break
                        
                        if not link and links:
                            link = links[0].get('href', '')
                            
                        # Only add if we have a role and a link
                        if role and link:
                            jobs.append({
                                'title': role,
                                'company': current_company,
                                'location': location,
                                'url': link,
                                'source': 'SimplifyJobs_GitHub'
                            })
                            
        print(f"Parsed {len(jobs)} jobs from community list.")
        return jobs

    def scrape_all(self):
        all_jobs = []
        for source_name, url in self.sources.items():
            print(f"Scraping source: {source_name}")
            jobs = self.scrape_simplify(url)
            all_jobs.extend(jobs)
        return all_jobs

if __name__ == "__main__":
    scraper = CommunityScraper()
    jobs = scraper.scrape_all()
    print("\n--- Scraped Community Jobs Summary ---")
    for job in jobs[:5]: # Print first 5 for testing
        print(f"- {job['title']} at {job['company']}")
    print(f"Total jobs scraped: {len(jobs)}")
