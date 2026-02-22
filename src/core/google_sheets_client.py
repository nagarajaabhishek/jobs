import json
import os
import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd

# Local JD cache path (JDs used for evaluation only; not stored in Sheets)
DEFAULT_JD_CACHE_PATH = os.path.join(os.getcwd(), "config", "jd_cache.json")

# Sort priority for Match Type (lower = higher priority). Includes Scoring 2.0 emoji verdicts.
SORT_PRIORITY_MAP = {
    "for sure": 1,
    "worth trying": 2,
    "ambitious": 3,
    "maybe": 4,
    "not at all": 5,
    "already seen": 6,
    "🔥 auto-apply": 1,
    "✅ strong match": 2,
    "⚖️ worth considering": 3,
    "❌ no": 5,
}


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
    def __init__(self, credentials_path="config/credentials.json", sheet_name="Resume_Agent_Jobs", jd_cache_path=None):
        self.credentials_path = credentials_path
        self.sheet_name = sheet_name
        self.jd_cache_path = jd_cache_path or os.environ.get("JD_CACHE_PATH", DEFAULT_JD_CACHE_PATH)
        self.client = None
        self.sheet = None
        self._cached_existing_urls = None

    def _load_jd_cache(self):
        """Load JD cache from file (canonical_url -> description)."""
        if not os.path.isfile(self.jd_cache_path):
            return {}
        try:
            with open(self.jd_cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_jd_cache(self, cache):
        os.makedirs(os.path.dirname(self.jd_cache_path) or ".", exist_ok=True)
        with open(self.jd_cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=0)

    def get_jd_for_url(self, url):
        """Return full JD for evaluation. Not stored in Sheets; read from local cache."""
        canonical = normalize_job_url(url or "")
        if not canonical:
            return ""
        cache = self._load_jd_cache()
        return cache.get(canonical, "") or ""

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
                    "Apply Score",     # H
                    "Match Type",      # I
                    "Recommended Resume", # J
                    "H1B Sponsorship", # K
                    "Location Verification", # L
                    "Missing Skills",  # M
                    "Applied? (Y/N)",   # N
                    "Job Description"  # O
                ]
                self.sheet.append_row(headers)
                
                # Format headers
                self.sheet.format('A1:O1', {'textFormat': {'bold': True}})



                
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

    def _get_or_create_col_index(self, worksheet, col_name, headers=None):
        """Helper to find or create a column by name and return its 1-based index."""
        if headers is None:
            headers = [h.strip() for h in worksheet.row_values(1)]
        
        if col_name in headers:
            return headers.index(col_name) + 1
        else:
            headers.append(col_name)
            col_idx = len(headers)
            worksheet.update_cell(1, col_idx, col_name)
            worksheet.format(f'{gspread.utils.rowcol_to_a1(1, col_idx)}', {'textFormat': {'bold': True}})
            return col_idx

    def add_jobs(self, jobs_list):
        """
        Adds new jobs. Skips duplicates and includes AI-sourced tags if available.
        """
        if not self.sheet:
            self.connect()
        
        existing = self.get_existing_urls()
        applied = self.get_applied_urls()
        seen = existing | applied
        
        # Get/Create headers for dynamic fields
        headers = [h.strip() for h in self.sheet.row_values(1)]
        tags_col = self._get_or_create_col_index(self.sheet, "Sourcing Tags", headers)
        
        new_rows = []
        jd_cache_updates = {}
        for job in jobs_list:
            canonical = normalize_job_url(job.get("url") or "")
            if not canonical or canonical in seen:
                continue
            
            desc = (job.get("description") or "").strip()
            if desc:
                jd_cache_updates[canonical] = desc[:50000]
            
            # Basic row structure (Fixed A-G)
            row = [""] * max(tags_col, 13) # ensure enough space
            row[0] = "NEW"
            row[1] = job.get("title", "")
            row[2] = job.get("company", "")
            row[3] = job.get("location", "")
            row[4] = job.get("url", "")
            row[5] = job.get("source", "Unknown")
            row[6] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Add Tags at the dynamic index
            if tags_col > 0:
                row[tags_col - 1] = job.get("tags", "")
                
            new_rows.append(row)
            seen.add(canonical)
            
        if new_rows:
            self.sheet.append_rows(new_rows)
            self._cached_existing_urls = seen
            if jd_cache_updates:
                cache = self._load_jd_cache()
                cache.update(jd_cache_updates)
                self._save_jd_cache(cache)
            print(f"Added {len(new_rows)} new jobs with AI Tags.")
        else:
            print("No new jobs to add.")

    def get_new_jobs(self, limit=100):
        """Fetches up to `limit` jobs that have the 'NEW' status from today's tab."""
        return self._get_jobs_by_criteria({'Status': 'NEW'}, limit)

    def get_maybe_jobs(self, limit=100):
        """Fetches up to `limit` jobs that have the 'Maybe' status from ALL tabs."""
        if not self.client:
            self.connect()
        try:
            spreadsheet = self.client.open(self.sheet_name)
            all_maybe_jobs = []
            # Start from newest worksheet first (reverse order)
            for worksheet in reversed(spreadsheet.worksheets()):
                values = worksheet.get_all_values()
                if not values:
                    continue
                headers = values[0]
                # Filter out empty records or handle duplicate empty headers
                records = []
                if len(values) > 1:
                    column_count = len(headers)
                    for i, row in enumerate(values[1:]):
                        # Construct a dict manually to avoid the gspread duplicate header issue
                        record = {}
                        for j, h in enumerate(headers):
                            if h and j < len(row):
                                record[h] = row[j]
                        
                        status = str(record.get('Status', '')).strip()
                        match_type = str(record.get('Match Type', '')).strip().replace('*', '')
                        if status == 'EVALUATED' and match_type == 'Maybe':
                            record['_row_index'] = i + 2
                            record['_worksheet'] = worksheet
                            all_maybe_jobs.append(record)
                            if len(all_maybe_jobs) >= limit:
                                return all_maybe_jobs, worksheet
            return all_maybe_jobs, None
        except Exception as e:
            print(f"Error fetching Maybe jobs: {e}")
            return [], None

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
        """
        headers = [h.strip() for h in worksheet.row_values(1)]
        
        match_col = self._get_or_create_col_index(worksheet, "Match Type", headers)
        score_col = self._get_or_create_col_index(worksheet, "Apply Score", headers)
        resume_col = self._get_or_create_col_index(worksheet, "Recommended Resume", headers)
        h1b_col = self._get_or_create_col_index(worksheet, "H1B Sponsorship", headers)
        loc_col = self._get_or_create_col_index(worksheet, "Location Verification", headers)
        skills_col = self._get_or_create_col_index(worksheet, "Missing Skills", headers)
        
        cells_to_update = []
        for row_index, match_type, recommended, h1b, loc_ver, missing, score in updates:
            cells_to_update.append(gspread.Cell(row=row_index, col=1, value="EVALUATED"))
            cells_to_update.append(gspread.Cell(row=row_index, col=match_col, value=match_type))
            cells_to_update.append(gspread.Cell(row=row_index, col=score_col, value=score))
            cells_to_update.append(gspread.Cell(row=row_index, col=resume_col, value=recommended))
            cells_to_update.append(gspread.Cell(row=row_index, col=h1b_col, value=h1b))
            cells_to_update.append(gspread.Cell(row=row_index, col=loc_col, value=loc_ver))
            cells_to_update.append(gspread.Cell(row=row_index, col=skills_col, value=missing))

            
        if cells_to_update:
            worksheet.update_cells(cells_to_update)
            print(f"Successfully updated {len(updates)} jobs with evaluations.")

    def get_sort_key_for_row(self, row, headers):
        """
        Return sort key (tuple) for a sheet row. Primary: Apply Score desc; secondary: Match Type priority; tertiary: PM boost.
        Uses SORT_PRIORITY_MAP so emoji verdicts (Scoring 2.0) sort correctly when score is missing.
        """
        match_col_idx = headers.index("Match Type") if "Match Type" in headers else -1
        score_col_idx = headers.index("Apply Score") if "Apply Score" in headers else -1
        role_col_idx = headers.index("Role Title") if "Role Title" in headers else -1
        rec_col_idx = headers.index("Recommended Resume") if "Recommended Resume" in headers else -1

        score = 0
        if score_col_idx != -1 and len(row) > score_col_idx:
            try:
                score = int(str(row[score_col_idx]).strip())
            except ValueError:
                score = 0

        if match_col_idx == -1 or len(row) <= match_col_idx:
            status_priority = 99
        else:
            match_val = row[match_col_idx].lower().strip().replace('*', '')
            status_priority = SORT_PRIORITY_MAP.get(match_val, 99)

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
        return (-score, status_priority, pm_boost)

    def sort_daily_jobs(self):
        """
        Sorts today's sheet rows based on the 'Match Type' evaluation priority.
        Primary sort: Apply Score (desc). Secondary: Match Type (incl. 🔥/✅/⚖️/❌). Tertiary: PM boost.
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
            
            if "Match Type" not in headers:
                print("No 'Match Type' column found. Skipping sort.")
                return

            rows.sort(key=lambda row: self.get_sort_key_for_row(row, headers))

            
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
