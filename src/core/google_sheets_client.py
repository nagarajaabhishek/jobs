import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd


def normalize_job_url(url):
    """
    Canonical form for duplicate detection: strip fragment, tracking params, trailing slash.
    Same job with different UTM or ref will match.
    """
    if not url or not isinstance(url, str):
        return ""
    url = url.strip()
    try:
        parsed = urlparse(url)
        # Drop fragment
        netloc = (parsed.netloc or "").lower()
        path = (parsed.path or "/").rstrip("/") or "/"
        # Keep only non-tracking query params (drop utm_*, ref, source, etc.)
        qs = parse_qs(parsed.query, keep_blank_values=False)
        skip_keys = {k.lower() for k in qs if re.match(r"^(utm_|ref|source|fbclid|gclid|mc_|_ga)$", k.lower()) or k.lower().startswith("utm_")}
        clean_qs = {k: v for k, v in qs.items() if k.lower() not in skip_keys}
        query = urlencode(clean_qs, doseq=True) if clean_qs else ""
        return urlunparse((parsed.scheme or "https", netloc, path, parsed.params, query, ""))
    except Exception:
        return url


class GoogleSheetsClient:
    def __init__(self, credentials_path="config/credentials.json", sheet_name="Resume_Agent_Jobs"):
        self.credentials_path = credentials_path
        self.sheet_name = sheet_name
        self.client = None
        self.sheet = None
        self._cached_existing_urls = None  # Avoid re-fetching all worksheets on every add_jobs()

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
                    "Status",          # A
                    "Role Title",      # B
                    "Company",         # C
                    "Location",        # D
                    "Job Link",        # E
                    "Source",          # F
                    "Date Added",      # G
                    "Match Type",      # H
                    "Recommended Resume", # I
                    "H1B Sponsorship", # J
                    "Location Verification", # K
                    "Missing Skills",  # L
                    "Applied? (Y/N)",   # M
                    "Job Description"  # N
                ]
                self.sheet.append_row(headers)
                
                # Format headers
                self.sheet.format('A1:N1', {'textFormat': {'bold': True}})



                
        except FileNotFoundError:
            raise FileNotFoundError(f"Credentials file not found at {self.credentials_path}. Please place your Google Service Account JSON key here.")

    def get_all_jobs(self):
        """Fetches all jobs from the sheet."""
        if not self.sheet:
            self.connect()
        return self.sheet.get_all_records()

    def get_existing_urls(self, use_cache=True):
        """Returns a set of canonical (normalized) Job Links from all tabs. Used to avoid adding duplicates."""
        if not self.client:
            self.connect()
        if use_cache and self._cached_existing_urls is not None:
            return self._cached_existing_urls
        existing_urls = set()
        try:
            spreadsheet = self.client.open(self.sheet_name)
            for worksheet in spreadsheet.worksheets():
                values = worksheet.get_all_values()
                if not values:
                    continue
                headers = values[0]
                url_index = next((i for i, h in enumerate(headers) if str(h).strip().lower() == "job link"), -1)
                if url_index != -1:
                    for row in values[1:]:
                        if len(row) > url_index and row[url_index]:
                            existing_urls.add(normalize_job_url(row[url_index]))
        except Exception as e:
            print(f"Error fetching existing URLs: {e}")
        self._cached_existing_urls = existing_urls
        return existing_urls

    def get_applied_urls(self):
        """Returns a set of canonical Job Links where user marked Applied? (Y/N) = Y. So we never re-add or re-evaluate those."""
        if not self.client:
            self.connect()
        applied = set()
        try:
            spreadsheet = self.client.open(self.sheet_name)
            applied_col = None
            url_index = None
            for worksheet in spreadsheet.worksheets():
                values = worksheet.get_all_values()
                if not values:
                    continue
                headers = [str(h).strip().lower() for h in values[0]]
                url_index = next((i for i, h in enumerate(headers) if h == "job link"), -1)
                applied_col = next((i for i, h in enumerate(values[0]) if "applied" in str(h).lower()), -1)
                if url_index == -1 or applied_col == -1:
                    continue
                for row in values[1:]:
                    if len(row) > max(url_index, applied_col):
                        applied_val = str(row[applied_col]).strip().upper()
                        if applied_val == "Y" or applied_val.startswith("Y"):
                            link = row[url_index]
                            if link:
                                applied.add(normalize_job_url(link))
        except Exception as e:
            print(f"Error fetching applied URLs: {e}")
        return applied

    def get_already_evaluated_or_applied_canonical_urls(self):
        """
        Canonical URLs of jobs that are already EVALUATED or marked Applied=Y in any tab.
        Use in evaluator to skip re-evaluating so the agent and user don't process the same job again.
        """
        if not self.client:
            self.connect()
        seen = set()
        try:
            spreadsheet = self.client.open(self.sheet_name)
            for worksheet in spreadsheet.worksheets():
                values = worksheet.get_all_values()
                if not values:
                    continue
                headers = [str(h).strip() for h in values[0]]
                url_idx = next((i for i, h in enumerate(headers) if h.lower() == "job link"), -1)
                status_idx = next((i for i, h in enumerate(headers) if h.lower() == "status"), -1)
                applied_idx = next((i for i, h in enumerate(headers) if "applied" in h.lower()), -1)
                if url_idx == -1:
                    continue
                for row in values[1:]:
                    if len(row) <= url_idx or not row[url_idx]:
                        continue
                    status = str(row[status_idx]).strip().upper() if status_idx >= 0 and len(row) > status_idx else ""
                    applied = str(row[applied_idx]).strip().upper() if applied_idx >= 0 and len(row) > applied_idx else ""
                    if status == "EVALUATED" or applied.startswith("Y"):
                        seen.add(normalize_job_url(row[url_idx]))
        except Exception as e:
            print(f"Error fetching already-seen URLs: {e}")
        return seen

    def add_jobs(self, jobs_list):
        """
        Adds new jobs. Skips duplicates by canonical URL and skips jobs already applied to (Applied? = Y in any tab).
        """
        if not self.sheet:
            self.connect()
        existing = self.get_existing_urls()
        applied = self.get_applied_urls()
        seen = existing | applied
        new_rows = []
        jobs_added = []
        for job in jobs_list:
            canonical = normalize_job_url(job.get("url") or "")
            if not canonical or canonical in seen:
                continue
            row = [
                "NEW",
                job.get("title", ""),
                job.get("company", ""),
                job.get("location", ""),
                job.get("url", ""),
                job.get("source", "Unknown"),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "", "", "", "", "", "",  # H–M: Match Type, Recommended Resume, H1B, Loc Ver, Missing Skills, Applied?
                job.get("description", ""),
            ]
            new_rows.append(row)
            jobs_added.append(job)
            seen.add(canonical)
        if new_rows:
            self.sheet.append_rows(new_rows)
            self._cached_existing_urls = seen
            print(f"Added {len(new_rows)} new jobs (duplicates and already-applied skipped by canonical URL).")
        else:
            print("No new jobs to add (all duplicates or already applied).")

    def get_new_jobs(self, limit=100):
        """Fetches up to `limit` jobs that have the 'NEW' status from today's tab."""
        return self._get_jobs_by_criteria({'Status': 'NEW'}, limit)

    def get_maybe_jobs(self, limit=100):
        """Fetches up to `limit` jobs that have the 'Maybe' status from today's tab."""
        return self._get_jobs_by_criteria({'Status': 'EVALUATED', 'Match Type': 'Maybe'}, limit)

    def _get_jobs_by_criteria(self, criteria, limit=100):
        """Internal helper to fetch jobs based on column-value criteria."""
        if not self.client:
            self.connect()
            
        today_str = datetime.now().strftime("%Y-%m-%d")
        try:
            worksheet = self.client.open(self.sheet_name).worksheet(today_str)
            records = worksheet.get_all_records()
            
            filtered_jobs = []
            for i, record in enumerate(records):
                # Check all criteria
                match = True
                for key, val in criteria.items():
                    # Handle string-based criteria more flexibly
                    actual = str(record.get(key, '')).strip()
                    target = str(val).strip()
                    
                    if key == "Match Type":
                        # Match Type might have asterisks from LLM formatting
                        actual = actual.replace('*', '')
                        
                    if actual.lower() != target.lower():
                        match = False
                        break
                
                if match:
                    record['_row_index'] = i + 2
                    filtered_jobs.append(record)
                    if len(filtered_jobs) >= limit:
                        break
            return filtered_jobs, worksheet

        except Exception as e:
            print(f"Error fetching jobs with criteria {criteria}: {e}")
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
        h1b_col = get_or_create_col("H1B Sponsorship")
        loc_col = get_or_create_col("Location Verification")
        skills_col = get_or_create_col("Missing Skills")
        
        cells_to_update = []
        for row_index, match_type, recommended, h1b, loc_ver, missing in updates:
            cells_to_update.append(gspread.Cell(row=row_index, col=1, value="EVALUATED"))
            cells_to_update.append(gspread.Cell(row=row_index, col=match_col, value=match_type))
            cells_to_update.append(gspread.Cell(row=row_index, col=resume_col, value=recommended))
            cells_to_update.append(gspread.Cell(row=row_index, col=h1b_col, value=h1b))
            cells_to_update.append(gspread.Cell(row=row_index, col=loc_col, value=loc_ver))
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
                "not at all": 5,
                "already seen": 6,
            }
            
            if "Match Type" not in headers:
                print("No 'Match Type' column found. Skipping sort.")
                return
                
            match_col_idx = headers.index("Match Type")
            role_col_idx = headers.index("Role Title") if "Role Title" in headers else -1
            rec_col_idx = headers.index("Recommended Resume") if "Recommended Resume" in headers else -1
            
            def sort_key(row):
                if len(row) <= match_col_idx:
                    return (99, 99) # Push to bottom if malformed
                
                match_val = row[match_col_idx].lower().strip().replace('*', '')
                priority = priority_map.get(match_val, 99)
                
                # Secondary priority: Product Manager boost
                is_pm = False
                if role_col_idx != -1 and len(row) > role_col_idx:
                    title = row[role_col_idx].lower()
                    if "product manager" in title or "tpm" in title or "product owner" in title:
                        is_pm = True
                
                if rec_col_idx != -1 and len(row) > rec_col_idx:
                    rec = row[rec_col_idx].lower()
                    if "tpm" in rec or "po" in rec:
                        is_pm = True
                
                pm_boost = 0 if is_pm else 1
                return (priority, pm_boost)
                
            rows.sort(key=sort_key)

            
            # Clear existing data and rewrite sorted data
            worksheet.clear()
            worksheet.update([headers] + rows)
            
            # Re-apply bold styling to headers
            worksheet.format('A1:M1', {'textFormat': {'bold': True}})

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
