import os
import re
import time
import requests
from bs4 import BeautifulSoup
from google import genai
from google_sheets_client import GoogleSheetsClient
from dotenv import load_dotenv

load_dotenv()

class SponsorshipAgent:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            print("WARNING: GEMINI_API_KEY environment variable not found in .env file.")
            exit(1)
            
        self.client = genai.Client(api_key=self.api_key)
        self.sheets_client = GoogleSheetsClient()
        self.model_name = 'gemini-2.0-flash'
        
        # Strict prompt to evaluate ONLY visa sponsorship metrics
        self.system_prompt = """
        You are a highly analytical immigration and HR expert.
        The user is an international student on an F-1 Visa in the United States and WILL require H-1B sponsorship in the future.
        
        Your task is to analyze the provided Job Description text and determine if the company will sponsor a visa.
        
        RULES:
        1. If the text says "US Citizen", "Green Card", "No C2C", "No Sponsorship", "must be authorized to work in the US without sponsorship", return: NO
        2. If the text says "Sponsorship available", "H1B transfer", "Visa sponsorship", return: YES
        3. If there is absolutely no mention of work authorization or citizenship, return: UNKNOWN
        
        OUTPUT FORMAT:
        You must output ONLY ONE WORD: YES, NO, or UNKNOWN. Do not provide any other text.
        """

    def scrape_job_description(self, url):
        """Attempts to scrape the job description if the URL is valid."""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Try to extract meaningful text, ignoring scripts and styles
                for script in soup(["script", "style"]):
                    script.decompose()
                text = soup.get_text(separator=' ')
                return re.sub(r'\s+', ' ', text).strip()
            return None
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
            return None

    def evaluate_sponsorship(self, text):
        """Passes the description to the 3-tier LLM engine to extract sponsorship status."""
        result_text, engine = self.llm.generate_content(
            system_prompt=self.system_prompt,
            user_prompt=f"Analyze this job description:\n\n{text}"
        )
        
        if engine == "FAILED":
            return "Unknown"
            
        result = result_text.strip().upper()
        if "YES" in result: return "Yes"
        if "NO" in result: return "No"
        return "Unknown"

    def run_sponsorship_check(self):
        print("Fetching EVALUATED jobs from Google Sheets...")
        
        if not self.sheets_client.client:
            self.sheets_client.connect()
            
        today_str = time.strftime("%Y-%m-%d")
        worksheet = self.sheets_client.client.open(self.sheets_client.sheet_name).worksheet(today_str)
        records = worksheet.get_all_records()
        
        updates = []
        # Find which column corresponds to Sponsorship Check, if it exists. If not, add it.
        headers = worksheet.row_values(1)
        if "Sponsorship Check" not in headers:
            # Add new header at Column L
            worksheet.update_cell(1, 12, "Sponsorship Check")
            worksheet.format('L1', {'textFormat': {'bold': True}})
            sponsorship_col_idx = 12
        else:
            sponsorship_col_idx = headers.index("Sponsorship Check") + 1

        for i, record in enumerate(records):
            row_idx = i + 2
            status = record.get('Status', '')
            link = record.get('Job Link', '')
            current_sponsorship = record.get('Sponsorship Check', '')
            
            if status == 'EVALUATED' and not current_sponsorship and len(updates) < 100:
                print(f"Checking Sponsorship for: {record.get('Company')} - {record.get('Role Title')}")
                
                # 1. We assume no cached description in the sheet to keep the sheet lightweight, so we scrape live.
                description = self.scrape_job_description(link)
                
                if not description or len(description) < 100:
                    print("  -> Could not scrape a valid description. Marking Unknown.")
                    sponsorship = "Unknown"
                else:
                    sponsorship = self.evaluate_sponsorship(description)
                    print(f"  -> Result: {sponsorship}")
                
                # Add to batch updates
                import gspread
                updates.append(gspread.Cell(row=row_idx, col=sponsorship_col_idx, value=sponsorship))
                
                # Rate limit sleep
                time.sleep(3)
                
        if updates:
            print(f"Batch updating {len(updates)} rows with sponsorship data...")
            worksheet.update_cells(updates)
            print("Done!")
        else:
            print("No pending jobs needed a sponsorship check.")

if __name__ == "__main__":
    agent = SponsorshipAgent()
    agent.run_sponsorship_check()
