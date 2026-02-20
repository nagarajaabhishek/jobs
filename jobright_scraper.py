import requests
import re

class JobrightScraper:
    def __init__(self):
        self.sources = {
            "Jobright_Data_Analysis": "https://raw.githubusercontent.com/jobright-ai/2026-Data-Analysis-Internship/master/README.md",
            "Jobright_Business_Analyst": "https://raw.githubusercontent.com/jobright-ai/2026-Business-Analyst-Internship/master/README.md"
        }

    def extract_link_and_text(self, cell_content):
        """Extracts URL and text from a markdown link like [text](url), or returns text if no link."""
        match = re.search(r'\[(.*?)\]\((.*?)\)', cell_content)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        # If there's bold tags around the text or link, let's clean them
        text = cell_content.replace('**', '').strip()
        return text, ""

    def scrape_jobright(self, url):
        """
        Scrapes a Jobright-style GitHub repository README.
        These READMEs use standard Markdown tables.
        """
        print(f"Fetching Jobright list from {url}...")
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return []

        lines = response.text.split('\n')
        jobs = []
        is_table = False
        headers = []

        current_company = "Unknown"

        for line in lines:
            line = line.strip()
            if not line.startswith('|'):
                continue
            
            # Parsing markdown table row
            cols = [col.strip() for col in line.split('|')[1:-1]]
            
            # Skip empty lines or separator lines (e.g., |---|---|)
            if not cols or all(all(c == '-' for c in col) for col in cols):
                continue
            
            if not headers:
                # Assume first row with pipes is headers
                headers = [col.lower() for col in cols]
                continue

            if len(cols) >= 3 and 'job title' in headers:
                company_col = cols[0]
                role_col = cols[1]
                location = cols[2]

                company_text, company_link = self.extract_link_and_text(company_col)
                if company_text and company_text != '↳':
                    current_company = company_text
                
                role_text, role_link = self.extract_link_and_text(role_col)

                if role_text and role_link:
                    jobs.append({
                        'title': role_text,
                        'company': current_company,
                        'location': location,
                        'url': role_link,
                        'source': 'JobrightAI_GitHub'
                    })

        print(f"Parsed {len(jobs)} jobs from Jobright list.")
        return jobs

    def scrape_all(self):
        all_jobs = []
        for source_name, url in self.sources.items():
            print(f"\nScraping source: {source_name}")
            jobs = self.scrape_jobright(url)
            all_jobs.extend(jobs)
        return all_jobs

if __name__ == "__main__":
    scraper = JobrightScraper()
    jobs = scraper.scrape_all()
    print("\n--- Scraped Jobright Jobs Summary ---")
    for job in jobs[:5]: # Print first 5 for testing
        print(f"- {job['title']} at {job['company']}")
    print(f"Total jobs scraped: {len(jobs)}")
