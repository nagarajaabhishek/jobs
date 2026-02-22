import requests

class ArbeitnowScraper:
    def __init__(self):
        self.base_url = "https://www.arbeitnow.com/api/job-board-api"

    def scrape(self, queries=["Software Engineer", "Machine Learning Engineer"]):
        """
        Scrapes jobs from Arbeitnow's free public API.
        """
        all_jobs = []

        for query in queries:
            print(f"Fetching from Arbeitnow API for '{query}'...")
            try:
                # The API supports 'search' parameter, although we might need to paginate if we want more
                response = requests.get(f"{self.base_url}?search={query}")
                response.raise_for_status()
                data = response.json()
                
                jobs = data.get('data', [])
                
                for job in jobs:
                    # 'remote' is a boolean, determine full location string
                    location = job.get('location', '')
                    if job.get('remote'):
                        location = f"Remote, {location}" if location else "Remote"
                        
                    all_jobs.append({
                        'title': job.get('title'),
                        'company': job.get('company_name'),
                        'location': location,
                        'url': job.get('url'),
                        'source': 'Arbeitnow_API'
                    })
                    
                print(f"Found {len(jobs)} jobs for '{query}'.")
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching Arbeitnow API: {e}")
                
        return all_jobs

if __name__ == "__main__":
    scraper = ArbeitnowScraper()
    jobs = scraper.scrape(queries=["Python", "Data"])
    print("\n--- Scraped Arbeitnow Jobs Summary ---")
    for job in jobs[:5]: # Print first 5 for testing
        print(f"- {job['title']} at {job['company']}")
    print(f"Total jobs scraped: {len(jobs)}")
