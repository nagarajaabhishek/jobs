import requests

class ATS_Scraper:
    def __init__(self):
        # We need a list of known company boards for greenhouse and lever
        # These are usually the 'clientname' parameter
        self.greenhouse_boards = ["canva", "discord", "figma"] # examples
        self.lever_boards = ["netflix", "palantir", "discord"] # examples

    def scrape_greenhouse(self, board_token):
        """Scrapes jobs from Greenhouse Board API v1."""
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        all_jobs = []
        try:
            print(f"Fetching from Greenhouse API for {board_token}...")
            response = requests.get(url)
            # If 404, it means the board_token is wrong or they disabled it
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()
            jobs = data.get('jobs', [])
            
            for job in jobs:
                location = job.get('location', {}).get('name', 'Unknown')
                all_jobs.append({
                    'title': job.get('title'),
                    'company': board_token.capitalize(), # Best guess unless we hit the standard /boards API first
                    'location': location,
                    'url': job.get('absolute_url'),
                    'source': 'ATS_Greenhouse'
                })
            print(f"Parsed {len(jobs)} jobs for {board_token}.")
        except Exception as e:
            print(f"Error fetching Greenhouse board {board_token}: {e}")
        return all_jobs

    def scrape_lever(self, site_token):
        """Scrapes jobs from Lever API v0."""
        # Note: Lever API v0 doesn't always require auth for public postings
        url = f"https://api.lever.co/v0/postings/{site_token}"
        all_jobs = []
        try:
            print(f"Fetching from Lever API for {site_token}...")
            response = requests.get(url)
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()
            
            for job in data:
                location = job.get('categories', {}).get('location', 'Unknown')
                all_jobs.append({
                    'title': job.get('text'), # Lever uses "text" for the job title
                    'company': site_token.capitalize(),
                    'location': location,
                    'url': job.get('hostedUrl'),
                    'source': 'ATS_Lever'
                })
            print(f"Parsed {len(data)} jobs for {site_token}.")
        except Exception as e:
            print(f"Error fetching Lever board {site_token}: {e}")
        return all_jobs

    def scrape_all(self):
        all_jobs = []
        for board in self.greenhouse_boards:
            all_jobs.extend(self.scrape_greenhouse(board))
        for board in self.lever_boards:
            all_jobs.extend(self.scrape_lever(board))
        return all_jobs

if __name__ == "__main__":
    scraper = ATS_Scraper()
    jobs = scraper.scrape_all()
    print("\n--- Scraped ATS Jobs Summary ---")
    for job in jobs[:5]: # Print first 5 for testing
        print(f"- {job['title']} at {job['company']}")
    print(f"Total jobs scraped: {len(jobs)}")
