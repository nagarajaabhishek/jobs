import requests # type: ignore
from bs4 import BeautifulSoup # type: ignore
import json
import logging
import urllib.parse
import time

class DiceScraper:
    """
    A scraper for Dice.com job listings.
    Dice's web search provides a robust way to find tech jobs.
    """
    def __init__(self):
        self.search_url = "https://www.dice.com/jobs"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.dice.com/"
        }

    def scrape(self, queries=None, locations=None, limit=20):
        """
        Scrapes Dice.com for the given queries and locations.
        """
        if not queries:
            queries = ["Product Manager"]
        if not locations:
            locations = ["Remote"]

        all_jobs = []
        for query in queries:
            for loc in locations:
                logging.info(f"DiceScraper: Searching for '{query}' in '{loc}'")
                try:
                    jobs = self._search_once(query, loc, limit)
                    all_jobs.extend(jobs)
                    # Respectful delay
                    time.sleep(1)
                except Exception as e:
                    logging.error(f"DiceScraper: Error searching for '{query}': {e}")
        
        return all_jobs

    def _search_once(self, query, location, limit):
        params = {
            "q": query,
            "location": location,
            "pageSize": limit,
            "filters.isRemote": "true" if "remote" in location.lower() else "false"
        }
        encoded_params = urllib.parse.urlencode(params)
        url = f"{self.search_url}?{encoded_params}"
        
        response = requests.get(url, headers=self.headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Dice often stores job data in a JSON object inside a script tag 
        # or inside a 'd-job-card' component.
        # We will look for a common pattern.
        jobs = []
        
        # Look for the job cards
        cards = soup.select('d-job-card')
        if not cards:
            # Fallback search for older/different UI elements
            cards = soup.select('.card.search-card')
            
        for card in cards:
            try:
                # Dice cards usually have data attributes or nested links
                title_elem = card.select_one('.card-title-link') or card.select_one('a[id^="job-title-"]')
                company_elem = card.select_one('.card-company a') or card.select_one('a[data-cy="search-result-company-name"]')
                loc_elem = card.select_one('.card-location') or card.select_one('.job-location')
                
                if title_elem:
                    url = title_elem.get('href', "")
                    if url and not url.startswith('http'):
                        url = "https://www.dice.com" + url
                        
                    jobs.append({
                        "title": title_elem.get_text(strip=True),
                        "company": company_elem.get_text(strip=True) if company_elem else "Unknown",
                        "location": loc_elem.get_text(strip=True) if loc_elem else location,
                        "url": url,
                        "source": "Dice",
                        "description": "" # Full description requires separate fetch or extraction from script
                    })
            except Exception as e:
                logging.debug(f"Error parsing Dice card: {e}")
                
        # If no cards found via selectors, try to find the hidden JSON data
        if not jobs:
            script_tag = soup.find('script', id='__NEXT_DATA__')
            if script_tag:
                try:
                    data = json.loads(script_tag.string)
                    # Traverse the JSON to find job results
                    # (Standard pattern for Next.js apps)
                    # Note: Dice's structure might vary, this is an estimate.
                    results = data.get('props', {}).get('pageProps', {}).get('searchResults', {}).get('jobs', [])
                    for job_data in results:
                        jobs.append({
                            "title": job_data.get('title'),
                            "company": job_data.get('company', {}).get('name'),
                            "location": job_data.get('location', {}).get('name'),
                            "url": "https://www.dice.com/jobs/detail/" + job_data.get('id'),
                            "source": "Dice",
                            "description": ""
                        })
                except:
                    pass
                    
        return jobs[:limit] # type: ignore

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = DiceScraper()
    jobs = scraper.scrape(queries=["Product Manager"], locations=["Remote"], limit=5)
    print(f"Found {len(jobs)} jobs from Dice.")
    for j in jobs:
        print(f"- {j['title']} at {j['company']} ({j['location']})")
