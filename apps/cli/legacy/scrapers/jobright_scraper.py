import re
import requests

from apps.cli.legacy.core.config import get_sourcing_config

_RAW_README = "https://raw.githubusercontent.com/jobright-ai/{repo}/master/README.md"


def _sources_from_repo_slugs(repos: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for repo in repos:
        slug = str(repo).strip()
        if not slug:
            continue
        label = f"Jobright_{slug.replace('-', '_')}"
        out[label] = _RAW_README.format(repo=slug)
    return out


class JobrightScraper:
    """
    Pulls job rows from selected jobright-ai GitHub README tables only.
    Repo list: config/pipeline.yaml → sourcing.jobright_github_repos (see defaults in config.py).
    """

    def __init__(self):
        raw = get_sourcing_config().get("jobright_github_repos")
        if isinstance(raw, list) and len(raw) == 0:
            self.sources = {}
            print("Jobright GitHub: jobright_github_repos is [] — no README feeds will be fetched.")
            return
        if isinstance(raw, list):
            repos = [str(x).strip() for x in raw if str(x).strip()]
        else:
            repos = []
        if not repos:
            print("Jobright GitHub: jobright_github_repos missing/invalid — no README feeds.")
            self.sources = {}
            return
        self.sources = _sources_from_repo_slugs(repos)


    def extract_link_and_text(self, cell_content):
        """Extracts URL and text from a markdown link like [text](url), or returns text if no link."""
        match = re.search(r'\[(.*?)\]\((.*?)\)', cell_content)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        # If there's bold tags around the text or link, let's clean them
        text = cell_content.replace('**', '').strip()
        return text, ""

    def _fetch_readme_text(self, url: str) -> str:
        """GET raw README; if default branch is main, retry after 404 on master."""
        print(f"Fetching Jobright list from {url}...")
        r = requests.get(url, timeout=30)
        if r.status_code == 404 and "/master/README.md" in url:
            alt = url.replace("/master/README.md", "/main/README.md")
            print(f"  master 404, trying {alt}...")
            r = requests.get(alt, timeout=30)
        r.raise_for_status()
        return r.text

    def scrape_jobright(self, url):
        """
        Scrapes a Jobright-style GitHub repository README.
        These READMEs use standard Markdown tables.
        """
        try:
            text = self._fetch_readme_text(url)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return []

        lines = text.split("\n")
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
