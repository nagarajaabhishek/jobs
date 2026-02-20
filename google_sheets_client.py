import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd

class GoogleSheetsClient:
    def __init__(self, credentials_path="credentials.json", sheet_name="Resume_Agent_Jobs"):
        self.credentials_path = credentials_path
        self.sheet_name = sheet_name
        self.client = None
        self.sheet = None

    def connect(self):
        """Authenticates with Google Sheets API and selects today's tab."""
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_path, scope)
            self.client = gspread.authorize(creds)
            
            # Determine today's date for the tab name
            today_str = datetime.now().strftime("%Y-%m-%d")
            
            try:
                # Open the entire spreadsheet document
                spreadsheet = self.client.open(self.sheet_name)
            except gspread.exceptions.SpreadsheetNotFound:
                print(f"Spreadsheet '{self.sheet_name}' not found. Creating it...")
                spreadsheet = self.client.create(self.sheet_name)
            
            try:
                # Try to get the worksheet for today
                self.sheet = spreadsheet.worksheet(today_str)
                print(f"Connected to sheet: {self.sheet_name}, tab: {today_str}")
            except gspread.exceptions.WorksheetNotFound:
                print(f"Tab for '{today_str}' not found. Creating it...")
                self.sheet = spreadsheet.add_worksheet(title=today_str, rows="100", cols="20")
                
                headers = [
                    "Status",          # A (NEW, SCRAPED, EVALUATED)
                    "Role Title",      # B
                    "Company",         # C
                    "Location",        # D
                    "Job Link",        # E
                    "Source",          # F
                    "Date Added",      # G
                    "Match Type",      # H (Not at all, Maybe, Ambitious, Worth Trying, For sure)
                    "Recommended Resume", # I (PM, PO, BA, SM, Manager, GTM)
                    "Missing Skills",  # J
                    "Applied? (Y/N)"   # K
                ]
                self.sheet.append_row(headers)
                
                # Format headers
                self.sheet.format('A1:K1', {'textFormat': {'bold': True}})
                
        except FileNotFoundError:
            raise FileNotFoundError(f"Credentials file not found at {self.credentials_path}. Please place your Google Service Account JSON key here.")

    def get_all_jobs(self):
        """Fetches all jobs from the sheet."""
        if not self.sheet:
            self.connect()
        return self.sheet.get_all_records()

    def get_existing_urls(self):
        """Returns a set of all Job Links currently in all sheets to prevent duplicates across days."""
        if not self.client:
            self.connect()
            
        existing_urls = set()
        try:
            spreadsheet = self.client.open(self.sheet_name)
            for worksheet in spreadsheet.worksheets():
                values = worksheet.get_all_values()
                if not values:
                    continue
                    
                headers = values[0]
                url_index = -1
                for i, h in enumerate(headers):
                    if h.strip().lower() == 'job link':
                        url_index = i
                        break
                        
                if url_index != -1:
                    for row in values[1:]:
                        if len(row) > url_index and row[url_index]:
                            existing_urls.add(row[url_index])
        except Exception as e:
            print(f"Error fetching existing URLs: {e}")
            
        return existing_urls

    def add_jobs(self, jobs_list):
        """
        Adds a list of new jobs to the sheet.
        jobs_list: List of dicts matching the schema.
        """
        if not self.sheet:
            self.connect()
            
        existing_links = self.get_existing_urls()
        new_rows = []
        
        for job in jobs_list:
            if job['url'] not in existing_links:
                row = [
                    "NEW",                  # A: Status
                    job.get('title', ''),   # B: Role Title
                    job.get('company', ''), # C: Company
                    job.get('location', ''),# D: Location
                    job.get('url', ''),     # E: Job Link
                    job.get('source', 'Unknown'), # F: Source
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # G: Date Added
                    "",                     # H: Match Type (Evaluation pending)
                    "",                     # I: Recommended Resume (Evaluation pending)
                    "",                     # J: Missing Skills (Evaluation pending)
                    ""                      # K: Applied? (Y/N)
                ]
                new_rows.append(row)
        
        if new_rows:
            self.sheet.append_rows(new_rows)
            print(f"Added {len(new_rows)} new jobs.")
        else:
            print("No new jobs to add.")

    def get_new_jobs(self, limit=100):
        """Fetches up to `limit` jobs that have the 'NEW' status from today's tab."""
        if not self.client:
            self.connect()
            
        today_str = datetime.now().strftime("%Y-%m-%d")
        try:
            worksheet = self.client.open(self.sheet_name).worksheet(today_str)
            records = worksheet.get_all_records()
            
            new_jobs = []
            # Row 1 is headers. record index 0 is row 2.
            for i, record in enumerate(records):
                if record.get('Status') == 'NEW':
                    record['_row_index'] = i + 2
                    new_jobs.append(record)
                    if len(new_jobs) >= limit:
                        break
            return new_jobs, worksheet
        except Exception as e:
            print(f"Error fetching new jobs: {e}")
            return [], None

    def update_evaluated_jobs(self, worksheet, updates):
        """
        Batch updates evaluated jobs to avoid rate limits.
        updates format: list of tuples (row_index, match_type, recommended_resume, missing_skills)
        """
        headers = worksheet.row_values(1)
        
        def get_or_create_col(col_name):
            if col_name in headers:
                return headers.index(col_name) + 1
            else:
                headers.append(col_name)
                worksheet.update_cell(1, len(headers), col_name)
                worksheet.format(f'{gspread.utils.rowcol_to_a1(1, len(headers))}', {'textFormat': {'bold': True}})
                return len(headers)
                
        match_col = get_or_create_col("Match Type")
        resume_col = get_or_create_col("Recommended Resume")
        skills_col = get_or_create_col("Missing Skills")
        
        cells_to_update = []
        for row_index, match_type, recommended, missing in updates:
            cells_to_update.append(gspread.Cell(row=row_index, col=1, value="EVALUATED"))
            cells_to_update.append(gspread.Cell(row=row_index, col=match_col, value=match_type))
            cells_to_update.append(gspread.Cell(row=row_index, col=resume_col, value=recommended))
            cells_to_update.append(gspread.Cell(row=row_index, col=skills_col, value=missing))
            
        if cells_to_update:
            worksheet.update_cells(cells_to_update)
            print(f"Successfully updated {len(updates)} jobs with evaluations.")

    def sort_daily_jobs(self):
        """
        Sorts today's sheet rows based on the 'Match Type' evaluation priority.
        1. For sure (Must apply)
        2. Worth Trying (Should apply)
        3. Ambitious (Maybe apply)
        4. Maybe 
        5. Not at all (Don't apply)
        """
        if not self.client:
            self.connect()
            
        today_str = datetime.now().strftime("%Y-%m-%d")
        try:
            worksheet = self.client.open(self.sheet_name).worksheet(today_str)
            values = worksheet.get_all_values()
            
            if len(values) <= 1:
                return # Only headers or empty
                
            headers = values[0]
            rows = values[1:]
            
            priority_map = {
                "for sure": 1,
                "worth trying": 2,
                "ambitious": 3,
                "maybe": 4,
                "not at all": 5
            }
            
            if "Match Type" not in headers:
                print("No 'Match Type' column found. Skipping sort.")
                return
                
            match_col_idx = headers.index("Match Type")
            
            def sort_key(row):
                if len(row) <= match_col_idx:
                    return 99 # Push to bottom if malformed
                
                match_val = row[match_col_idx].lower().strip().replace('*', '')
                return priority_map.get(match_val, 99)
                
            rows.sort(key=sort_key)
            
            # Clear existing data and rewrite sorted data
            worksheet.clear()
            worksheet.update([headers] + rows)
            
            # Re-apply bold styling to headers
            worksheet.format('A1:K1', {'textFormat': {'bold': True}})
            print("Successfully sorted Google Sheet by Evaluation Match Type.")
            
        except Exception as e:
            print(f"Error sorting jobs: {e}")

if __name__ == "__main__":
    # Test script
    client = GoogleSheetsClient()
    try:
        client.connect()
        print("Connection successful.")
    except Exception as e:
        print(f"Connection failed: {e}")
