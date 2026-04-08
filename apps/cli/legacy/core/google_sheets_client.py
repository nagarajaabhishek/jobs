import json
import os
import re
import time
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

import gspread
from gspread.utils import rowcol_to_a1
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd
from apps.cli.legacy.core.utils import cleanup_jd_cache
from apps.cli.legacy.core.config import get_sheet_config
from apps.cli.legacy.core.learning_schemas import (
    SHEET_COL_ACTION_LINK,
    SHEET_COL_BASE_LLM_SCORE,
    SHEET_COL_CALIBRATION_DELTA,
    SHEET_COL_DECISION_AUDIT,
    SHEET_COL_DIGEST_STATUS,
    SHEET_COL_EVIDENCE_JSON,
    SHEET_COL_FEEDBACK,
    SHEET_COL_FEEDBACK_NOTE,
    SHEET_COL_JD_FETCH_METHOD,
    SHEET_COL_JD_FETCH_REASON,
    SHEET_COL_JD_VERIFIED,
)

# Local JD cache path (JDs used for evaluation only; not stored in Sheets)
DEFAULT_JD_CACHE_PATH = os.path.join(os.getcwd(), "config", "jd_cache.json")

# New daily tabs must fit evaluation + learning columns (through "Action Link" ≈ column 21+).
DEFAULT_NEW_WORKSHEET_ROWS = 100
DEFAULT_NEW_WORKSHEET_COLS = 30

# Sort priority for Match Type (lower = higher priority). Includes Scoring 2.0 emoji verdicts.
SORT_PRIORITY_MAP = {
    "for sure": 1,
    "worth trying": 2,
    "ambitious": 3,
    "maybe": 4,
    "not at all": 5,
    "already seen": 6,
    "🔥 auto-apply": 1,
    "🚀 must-apply": 1,
    "✅ strong match": 2,
    "⚡ ambitious match": 3,
    "⚖️ worth considering": 3,
    "📉 low priority": 4,
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


def parse_spreadsheet_id(url_or_id):
    """Return a Google spreadsheet file ID, or None. Accepts a full Sheets URL or a raw ID."""
    if url_or_id is None:
        return None
    s = str(url_or_id).strip()
    if not s:
        return None
    if "/spreadsheets/d/" in s:
        part = s.split("/spreadsheets/d/")[1].split("/")[0].split("?")[0].strip()
        return part or None
    if re.fullmatch(r"[a-zA-Z0-9_-]+", s) and len(s) >= 20:
        return s
    return None


class GoogleSheetsClient:
    def __init__(
        self,
        credentials_path="config/credentials.json",
        sheet_name="Resume_Agent_Jobs",
        jd_cache_path=None,
        spreadsheet_id=None,
    ):
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass

        self.credentials_path = credentials_path
        self.sheet_name = sheet_name
        self.jd_cache_path = jd_cache_path or os.environ.get("JD_CACHE_PATH", DEFAULT_JD_CACHE_PATH)
        self.client = None
        self.sheet = None
        self._cached_existing_urls = None

        cfg_sheet = get_sheet_config()
        raw = spreadsheet_id
        if raw is None:
            raw = os.environ.get("GOOGLE_SHEET_ID") or os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID")
        if raw is None:
            raw = cfg_sheet.get("spreadsheet_id") or cfg_sheet.get("spreadsheet_url")
        self.spreadsheet_id = parse_spreadsheet_id(raw)
        
        # Run Janitor
        removed, migrated = cleanup_jd_cache(self.jd_cache_path)
        if removed > 0 or migrated > 0:
            print(f"🧹 JD Cache Janitor: Removed {removed} old entries, migrated {migrated} to new format.")

    def _open_workbook(self):
        """Open the configured spreadsheet by ID or title. Does not create a new file."""
        if self.spreadsheet_id:
            return self.client.open_by_key(self.spreadsheet_id)
        return self.client.open(self.sheet_name)

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
        data = cache.get(canonical, "")
        if isinstance(data, dict):
            return data.get("jd", "")
        return str(data) # Fallback for old format if somehow not migrated

    def connect(self):
        """Authenticates with Google Sheets API and selects today's tab."""
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_path, scope)
            self.client = gspread.authorize(creds)
            
            # Determine today's date for the tab name
            today_str = datetime.now().strftime("%Y-%m-%d")
            
            try:
                spreadsheet = self._open_workbook()
            except gspread.exceptions.SpreadsheetNotFound:
                if self.spreadsheet_id:
                    raise gspread.exceptions.SpreadsheetNotFound(
                        f"Spreadsheet not found for id {self.spreadsheet_id!r} "
                        "(check the ID and that the service account has Editor access)."
                    ) from None
                print(f"Spreadsheet '{self.sheet_name}' not found. Creating it...")
                spreadsheet = self.client.create(self.sheet_name)
            
            try:
                # Try to get the worksheet for today
                self.sheet = spreadsheet.worksheet(today_str)
                doc_label = getattr(spreadsheet, "title", None) or self.sheet_name
                print(f"Connected to spreadsheet '{doc_label}', tab: {today_str}")
            except gspread.exceptions.WorksheetNotFound:
                print(f"Tab for '{today_str}' not found. Creating it...")
                self.sheet = spreadsheet.add_worksheet(
                    title=today_str,
                    rows=str(DEFAULT_NEW_WORKSHEET_ROWS),
                    cols=str(DEFAULT_NEW_WORKSHEET_COLS),
                )
                
                # Core evaluation columns
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
                    "Reasoning",       # L
                    "Missing Skills",  # M
                    "Applied? (Y/N)",  # N
                    SHEET_COL_JD_VERIFIED,     # O
                    SHEET_COL_JD_FETCH_METHOD, # P
                    SHEET_COL_JD_FETCH_REASON, # Q
                ]

                # Apply / resume lifecycle columns for automation & tracking.
                headers.extend(
                    [
                        "Apply Bucket",    # R – MUST_APPLY / STRONG_MATCH / ...
                        "Apply Channel",   # S – ATS_GREENHOUSE / JOB_BOARD_LINKEDIN / OTHER
                        "Resume Status",   # T – NOT_GENERATED / GENERATED_PENDING_REVIEW / ...
                        "Resume Path",     # U – storage link or path
                        "Reviewer Notes",  # V – free-form human comments
                        "Apply Status",    # W – NOT_STARTED / READY_TO_APPLY / APPLYING / APPLIED / FAILED
                        "Apply Error",     # X – last failure reason if any
                        "Applied At",      # Y – timestamp of successful apply
                        "Apply Metadata",  # Z – JSON blob for adapter/state
                    ]
                )

                self.sheet.append_row(headers)
                
                # Format headers
                last_col_a1 = rowcol_to_a1(1, len(headers))
                self.sheet.format(f"A1:{last_col_a1}", {'textFormat': {'bold': True}})



                
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
            spreadsheet = self._open_workbook()
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
            spreadsheet = self._open_workbook()
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
            spreadsheet = self._open_workbook()
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
            if col_idx > worksheet.col_count:
                worksheet.resize(cols=max(col_idx + 2, DEFAULT_NEW_WORKSHEET_COLS))
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
        
        # Tags are no longer stored in Sheets; they are parsed only
        # Sourcing Tags column is redundant since we have Reasoning
        
        new_rows = []
        jd_meta_updates = []
        jd_cache_updates = {}
        for job in jobs_list:
            canonical = normalize_job_url(job.get("url") or "")
            if not canonical or canonical in seen:
                continue
            
            desc = (job.get("description") or "").strip()
            jd_verified = bool(job.get("jd_verified", False))
            jd_fetch_method = str(job.get("jd_fetch_method") or "")
            jd_fetch_reason = str(job.get("jd_fetch_reason") or "")

            if jd_verified and desc:
                jd_cache_updates[canonical] = {
                    "jd": desc[:50000],
                    "timestamp": datetime.now().strftime("%Y-%m-%d")
                }
            
            # Basic row structure (Fixed A-G)
            row = [""] * 17 # includes JD meta cols (O-Q)
            row[0] = "NEW" if jd_verified else "NO_JD"
            row[1] = job.get("title", "")
            row[2] = job.get("company", "")
            row[3] = job.get("location", "")
            row[4] = job.get("url", "")
            row[5] = job.get("source", "Unknown")
            row[6] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row[14] = "Y" if jd_verified else "N"
            row[15] = jd_fetch_method
            row[16] = jd_fetch_reason
            
            new_rows.append(row)
            jd_meta_updates.append((canonical, jd_verified, jd_fetch_method, jd_fetch_reason))
            seen.add(canonical)
            
        if new_rows:
            self._with_retries(lambda: self.sheet.append_rows(new_rows), op_name="append_rows")
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
            spreadsheet = self._open_workbook()
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
                        if status == 'EVALUATED' and match_type in ('Maybe', '⚖️ Worth Considering'):
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
            worksheet = self._open_workbook().worksheet(today_str)
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


    @staticmethod
    def _normalize_evaluation_update(u):
        """
        Accept legacy 8-tuple or extended 11-tuple:
        (row, match, rec, h1b, loc, missing, score, reasoning)
        (row, match, rec, h1b, loc, missing, score, reasoning, calibration_delta, decision_audit_json, base_llm_score)
        Or dict with those keys.
        """
        if isinstance(u, dict):
            d = u
            return {
                "row_index": int(d["row_index"]),
                "match_type": d.get("match_type", ""),
                "recommended": d.get("recommended", d.get("recommended_resume", "")),
                "h1b": d.get("h1b", ""),
                "loc_ver": d.get("loc_ver", d.get("location_verification", "")),
                "missing": d.get("missing", d.get("missing_skills", "")),
                "score": d.get("score", d.get("apply_score", 0)),
                "reasoning": d.get("reasoning", ""),
                "calibration_delta": int(d.get("calibration_delta", 0)),
                "decision_audit_json": str(d.get("decision_audit_json", "") or ""),
                "base_llm_score": d.get("base_llm_score"),
                "feedback": d.get("feedback", ""),
                "feedback_note": d.get("feedback_note", ""),
                "digest_status": d.get("digest_status", ""),
                "action_link": d.get("action_link", ""),
                # Optional role-aware judge + ATS fields (may be absent)
                "role_judge_score": d.get("role_judge_score"),
                "role_judge_verdict": d.get("role_judge_verdict", ""),
                "role_judge_notes": d.get("role_judge_notes", ""),
                "ats_match_pct": d.get("ats_match_pct"),
                "ats_critical_gaps": d.get("ats_critical_gaps", ""),
            }
        if len(u) == 8:
            row_index, match_type, recommended, h1b, loc_ver, missing, score, reasoning = u
            return {
                "row_index": row_index,
                "match_type": match_type,
                "recommended": recommended,
                "h1b": h1b,
                "loc_ver": loc_ver,
                "missing": missing,
                "score": score,
                "reasoning": reasoning,
                "calibration_delta": 0,
                "decision_audit_json": "",
                "base_llm_score": None,
                "feedback": "",
                "feedback_note": "",
                "digest_status": "",
                "action_link": "",
                "evidence_json": "",
            }
        if len(u) == 11:
            (
                row_index,
                match_type,
                recommended,
                h1b,
                loc_ver,
                missing,
                score,
                reasoning,
                calibration_delta,
                decision_audit_json,
                base_llm_score,
            ) = u
            return {
                "row_index": row_index,
                "match_type": match_type,
                "recommended": recommended,
                "h1b": h1b,
                "loc_ver": loc_ver,
                "missing": missing,
                "score": score,
                "reasoning": reasoning,
                "calibration_delta": int(calibration_delta),
                "decision_audit_json": str(decision_audit_json or ""),
                "base_llm_score": base_llm_score,
                "feedback": "",
                "feedback_note": "",
                "digest_status": "",
                "action_link": "",
                "evidence_json": "",
            }
        if len(u) == 12:
            (
                row_index,
                match_type,
                recommended,
                h1b,
                loc_ver,
                missing,
                score,
                reasoning,
                calibration_delta,
                decision_audit_json,
                base_llm_score,
                evidence_json,
            ) = u
            return {
                "row_index": row_index,
                "match_type": match_type,
                "recommended": recommended,
                "h1b": h1b,
                "loc_ver": loc_ver,
                "missing": missing,
                "score": score,
                "reasoning": reasoning,
                "calibration_delta": int(calibration_delta),
                "decision_audit_json": str(decision_audit_json or ""),
                "base_llm_score": base_llm_score,
                "feedback": "",
                "feedback_note": "",
                "digest_status": "",
                "action_link": "",
                "evidence_json": str(evidence_json or ""),
            }
        raise ValueError(f"Invalid evaluation update shape: len={len(u) if hasattr(u, '__len__') else 'n/a'}")

    def update_evaluated_jobs(self, worksheet, updates):
        """
        Batch updates evaluated jobs to avoid rate limits.
        Supports legacy 8-tuples or extended 11-tuples (calibration + audit).
        """
        headers = [h.strip() for h in worksheet.row_values(1)]

        match_col = self._get_or_create_col_index(worksheet, "Match Type", headers)
        score_col = self._get_or_create_col_index(worksheet, "Apply Score", headers)
        resume_col = self._get_or_create_col_index(worksheet, "Recommended Resume", headers)
        h1b_col = self._get_or_create_col_index(worksheet, "H1B Sponsorship", headers)
        reason_col = self._get_or_create_col_index(worksheet, "Reasoning", headers)
        skills_col = self._get_or_create_col_index(worksheet, "Missing Skills", headers)
        cal_col = self._get_or_create_col_index(worksheet, SHEET_COL_CALIBRATION_DELTA, headers)
        audit_col = self._get_or_create_col_index(worksheet, SHEET_COL_DECISION_AUDIT, headers)
        base_col = self._get_or_create_col_index(worksheet, SHEET_COL_BASE_LLM_SCORE, headers)
        ev_col = self._get_or_create_col_index(worksheet, SHEET_COL_EVIDENCE_JSON, headers)
        fb_col = self._get_or_create_col_index(worksheet, SHEET_COL_FEEDBACK, headers)
        fn_col = self._get_or_create_col_index(worksheet, SHEET_COL_FEEDBACK_NOTE, headers)
        dig_col = self._get_or_create_col_index(worksheet, SHEET_COL_DIGEST_STATUS, headers)
        act_col = self._get_or_create_col_index(worksheet, SHEET_COL_ACTION_LINK, headers)
        # New: bucketization column derived from Apply Score.
        bucket_col = self._get_or_create_col_index(worksheet, "Apply Bucket", headers)

        # New judge + ATS columns (created lazily; safe for old sheets)
        rj_score_col = self._get_or_create_col_index(worksheet, "Role Judge Score", headers)
        rj_verdict_col = self._get_or_create_col_index(worksheet, "Role Judge Verdict", headers)
        rj_notes_col = self._get_or_create_col_index(worksheet, "Role Judge Notes", headers)
        ats_match_col = self._get_or_create_col_index(worksheet, "ATS Match %", headers)
        ats_gaps_col = self._get_or_create_col_index(worksheet, "ATS Critical Gaps", headers)

        cells_to_update = []
        for raw in updates:
            u = self._normalize_evaluation_update(raw)
            row_index = u["row_index"]
            match_type = u["match_type"]
            recommended = u["recommended"]
            h1b = u["h1b"]
            loc_ver = u["loc_ver"]
            missing = u["missing"]
            score = u["score"]
            reasoning = u["reasoning"]

            # Note: loc_ver is passed but we merge into reasoning if it has nuance
            final_reason = reasoning
            if loc_ver and str(loc_ver).lower() not in ["confirmed", "unknown", "—", ""]:
                if not reasoning or reasoning == "N/A":
                    final_reason = f"LOC: {loc_ver}"
                else:
                    final_reason = f"[{loc_ver}] {reasoning}"

            cells_to_update.append(gspread.Cell(row=row_index, col=1, value="EVALUATED"))
            cells_to_update.append(gspread.Cell(row=row_index, col=match_col, value=match_type))
            cells_to_update.append(gspread.Cell(row=row_index, col=score_col, value=score))
            cells_to_update.append(gspread.Cell(row=row_index, col=resume_col, value=recommended))
            cells_to_update.append(gspread.Cell(row=row_index, col=h1b_col, value=h1b))
            cells_to_update.append(gspread.Cell(row=row_index, col=reason_col, value=final_reason))
            cells_to_update.append(gspread.Cell(row=row_index, col=skills_col, value=missing))
            cells_to_update.append(gspread.Cell(row=row_index, col=cal_col, value=u["calibration_delta"]))
            cells_to_update.append(gspread.Cell(row=row_index, col=audit_col, value=u["decision_audit_json"]))
            cells_to_update.append(gspread.Cell(row=row_index, col=ev_col, value=u.get("evidence_json") or ""))
            base_val = u["base_llm_score"]
            if base_val is None or base_val == "":
                base_val = ""
            else:
                base_val = int(base_val)
            cells_to_update.append(gspread.Cell(row=row_index, col=base_col, value=base_val))
            cells_to_update.append(gspread.Cell(row=row_index, col=fb_col, value=u.get("feedback") or ""))
            cells_to_update.append(gspread.Cell(row=row_index, col=fn_col, value=u.get("feedback_note") or ""))
            cells_to_update.append(gspread.Cell(row=row_index, col=dig_col, value=u.get("digest_status") or ""))
            cells_to_update.append(gspread.Cell(row=row_index, col=act_col, value=u.get("action_link") or ""))

            # Derive Apply Bucket from the final Apply Score using calibrated Conviction bands.
            try:
                numeric_score = int(score)
            except Exception:
                numeric_score = 0

            if numeric_score >= 90:
                apply_bucket = "MUST_APPLY"
            elif numeric_score >= 70:
                apply_bucket = "STRONG_MATCH"
            elif numeric_score >= 60:
                apply_bucket = "AMBITION_MATCH"
            else:
                apply_bucket = "SKIP"

            cells_to_update.append(gspread.Cell(row=row_index, col=bucket_col, value=apply_bucket))

            # Optional judge + ATS enrichment
            rj_score = u.get("role_judge_score")
            if rj_score is not None and rj_score != "":
                try:
                    rj_score_int = int(rj_score)
                except ValueError:
                    rj_score_int = ""
            else:
                rj_score_int = ""
            cells_to_update.append(gspread.Cell(row=row_index, col=rj_score_col, value=rj_score_int))
            cells_to_update.append(gspread.Cell(row=row_index, col=rj_verdict_col, value=u.get("role_judge_verdict") or ""))
            cells_to_update.append(gspread.Cell(row=row_index, col=rj_notes_col, value=u.get("role_judge_notes") or ""))

            ats_pct = u.get("ats_match_pct")
            if ats_pct is not None and ats_pct != "":
                try:
                    ats_pct_int = int(ats_pct)
                except ValueError:
                    ats_pct_int = ""
            else:
                ats_pct_int = ""
            cells_to_update.append(gspread.Cell(row=row_index, col=ats_match_col, value=ats_pct_int))
            cells_to_update.append(gspread.Cell(row=row_index, col=ats_gaps_col, value=u.get("ats_critical_gaps") or ""))

        if cells_to_update:
            self._with_retries(lambda: worksheet.update_cells(cells_to_update), op_name="update_cells")
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
            worksheet = self._open_workbook().worksheet(today_str)
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
            self._with_retries(lambda: worksheet.clear(), op_name="worksheet_clear")
            self._with_retries(lambda: worksheet.update([headers] + rows), op_name="worksheet_update")
            
            # Re-apply bold styling to headers
            last_col = max(1, len(headers))
            worksheet.format(f"A1:{rowcol_to_a1(1, last_col)}", {'textFormat': {'bold': True}})

            print("Successfully sorted Google Sheet by Evaluation Match Type.")
            
        except Exception as e:
            print(f"Error sorting jobs: {e}")

    def update_resume_for_row(
        self,
        worksheet,
        row_index: int,
        resume_path: str,
        resume_status: str = "GENERATED_PENDING_REVIEW",
        reviewer_notes: str = "",
    ):
        """
        Update resume-related lifecycle columns for a single row.

        This is used by the TailorAgent orchestration after generating a
        tailored resume artifact for a specific job.
        """
        headers = [h.strip() for h in worksheet.row_values(1)]

        resume_status_col = self._get_or_create_col_index(worksheet, "Resume Status", headers)
        resume_path_col = self._get_or_create_col_index(worksheet, "Resume Path", headers)
        reviewer_notes_col = self._get_or_create_col_index(worksheet, "Reviewer Notes", headers)

        cells = [
            gspread.Cell(row=row_index, col=resume_status_col, value=resume_status),
            gspread.Cell(row=row_index, col=resume_path_col, value=resume_path),
            gspread.Cell(row=row_index, col=reviewer_notes_col, value=reviewer_notes or ""),
        ]

        self._with_retries(
            lambda: worksheet.update_cells(cells),
            op_name="update_resume_for_row",
        )

    def _with_retries(self, fn, op_name="operation", retries=3, base_sleep=1.5):
        """Retry wrapper for transient Sheets API failures."""
        last_error = None
        for attempt in range(1, retries + 1):
            try:
                return fn()
            except Exception as e:
                last_error = e
                if attempt == retries:
                    raise
                sleep_s = base_sleep * attempt
                print(f"Retrying {op_name} ({attempt}/{retries}) after error: {e}")
                time.sleep(sleep_s)
        if last_error:
            raise last_error

if __name__ == "__main__":
    # Test script
    client = GoogleSheetsClient()
    try:
        client.connect()
        print("Connection successful.")
    except Exception as e:
        print(f"Connection failed: {e}")
