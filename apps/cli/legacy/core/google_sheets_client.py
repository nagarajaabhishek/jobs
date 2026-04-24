import json
import logging
import os
import re
import sys
import time
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

import gspread
from gspread.exceptions import APIError
from gspread.utils import ValueRenderOption, rowcol_to_a1
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd
from apps.cli.legacy.core.utils import cleanup_jd_cache
from apps.cli.legacy.core.config import get_sheet_config, get_worksheet_tab_date
from apps.cli.legacy.core import sheet_outbox
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

# When append_rows (or pre-append reads) fail, jobs are written here for offline replay.
DEFAULT_SHEET_APPEND_FALLBACK_DIR = os.path.join(os.getcwd(), "data", "sheet_append_fallback")

# Keys to persist for replay via scripts/tools/replay_sheet_fallback_queue.py
_FALLBACK_JOB_KEYS = (
    "url",
    "title",
    "company",
    "location",
    "source",
    "site",
    "description",
    "jd_verified",
    "jd_fetch_method",
    "jd_fetch_reason",
    "tags",
)

logger = logging.getLogger(__name__)

# Dedicated tab in the same spreadsheet: paste job URLs for JD fetch + resume tailoring (optional workflow).
DEFAULT_MANUAL_JD_TAILOR_TAB = "Manual_JD_Tailor"
# Last column on Manual_JD_Tailor: absolute path to generated PDF (or .tex if PDF missing).
MANUAL_TAILOR_RESUME_COL = "Resume (PDF)"

# Pull http(s) or www.… from a cell; Sheets hyperlinks sometimes store only visible title in FORMATTED_VALUE.
_MANUAL_TAILOR_URL_RE = re.compile(r"(https?://[^\s\)\]>'\"]+|www\.[^\s\)\]>'\"]+)", re.I)


def _as_list_of_lists(grid: object) -> list[list]:
    if grid is None:
        return []
    if isinstance(grid, list):
        return grid
    vals = getattr(grid, "values", None)
    if isinstance(vals, list):
        return vals
    return []


def _url_from_manual_tailor_cell(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    m = _MANUAL_TAILOR_URL_RE.search(s)
    if not m:
        return ""
    u = m.group(1).rstrip(").,;\\]}'\"")
    if u.lower().startswith("www."):
        u = "https://" + u[4:]
    return u


def _first_job_url_in_row(cells: list[str]) -> str:
    for c in cells:
        u = _url_from_manual_tailor_cell(str(c))
        if u:
            return u
    return ""


def _manual_tailor_first_row_is_header(first_row: list) -> bool:
    cells = [str(c).strip().lower() for c in first_row[:12]]
    return "job link" in cells

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


class SheetsReadError(RuntimeError):
    """Raised when Google Sheets reads fail after retries (e.g. persistent 429 quota)."""


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
        self._cached_applied_urls = None
        self._cached_evaluated_or_applied_urls = None
        self._worksheet_header_row_cache = {}
        self._last_sheets_call_end_monotonic = 0.0

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

    @staticmethod
    def invalidate_sheet_url_caches(client: "GoogleSheetsClient") -> None:
        """Clear cached URL sets so the next read hits Google Sheets."""
        client._cached_existing_urls = None
        client._cached_applied_urls = None
        client._cached_evaluated_or_applied_urls = None
        client._worksheet_header_row_cache = {}

    def _manual_jd_tailor_tab_title(self) -> str:
        cfg = get_sheet_config()
        return str(cfg.get("manual_jd_tailor_tab") or DEFAULT_MANUAL_JD_TAILOR_TAB).strip() or DEFAULT_MANUAL_JD_TAILOR_TAB

    def ensure_manual_jd_tailor_worksheet(self):
        """
        Create (if missing) a simple tab for pasting job URLs for JD ingestion / resume tailoring.
        Same spreadsheet as pipeline; does not replace daily sourcing tabs.
        """
        if not self.client:
            self.connect()
        spreadsheet = self._open_workbook()
        title = self._manual_jd_tailor_tab_title()
        try:
            ws = spreadsheet.worksheet(title)
            self._ensure_recommended_resume_column(ws)
            self._ensure_resume_pdf_column_last(ws)
            return ws
        except gspread.exceptions.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(
                title=title,
                rows=DEFAULT_NEW_WORKSHEET_ROWS,
                cols=14,
            )
            headers = [
                "Status",
                "Job Link",
                "Recommended Resume",
                "Notes",
                "Last processed",
                "Error",
                "Validation Verdict",
                "Validation Reason",
                "Tailored Score",
                "Generic Score",
                "Use Resume",
                MANUAL_TAILOR_RESUME_COL,
            ]
            ws.append_row(headers)
            last = rowcol_to_a1(1, len(headers))
            ws.format(f"A1:{last}", {"textFormat": {"bold": True}})
            print(
                f"Created tab '{title}' for manual JD URLs: "
                "B = Job Link; C = Suggested resume variant (optional); "
                "or paste URL-only in column A."
            )
            return ws

    def _ensure_recommended_resume_column(self, ws) -> None:
        """
        Older Manual_JD_Tailor tabs had no Recommended Resume column.
        Appends a new column at the end with header 'Recommended Resume' when missing.
        """
        row1 = self._with_retries(lambda: ws.row_values(1), op_name="manual_tailor_header_row") or []
        labels = [str(x).strip().lower() for x in row1 if str(x).strip()]
        if "recommended resume" in labels:
            return
        if not labels:
            return
        # Append after the last header cell (e.g. old layout ends at F Error → use column G)
        last_used = len(row1)
        new_col = last_used + 1
        if new_col > ws.col_count:
            self._with_retries(
                lambda: ws.resize(rows=max(ws.row_count, 100), cols=new_col),
                op_name="manual_tailor_resize_cols",
            )
        self._with_retries(
            lambda: ws.update_cell(1, new_col, "Recommended Resume"),
            op_name="manual_tailor_add_header",
        )
        a1 = rowcol_to_a1(1, new_col)
        self._with_retries(
            lambda: ws.format(a1, {"textFormat": {"bold": True}}),
            op_name="manual_tailor_format_header",
        )
        print(
            "[Manual_JD_Tailor] Added column 'Recommended Resume' at the end of row 1. "
            "Enter your suggested variant there (e.g. TPM vs PO from your other tool). "
            "Job links stay in column B."
        )

    def _ensure_resume_pdf_column_last(self, ws) -> None:
        """
        Ensure a rightmost 'Resume (PDF)' column exists (output artifact path).
        Legacy tabs may still have 'Tailored YAML'; we append Resume (PDF) at the end if missing.
        """
        row1 = self._with_retries(lambda: ws.row_values(1), op_name="manual_tailor_header_resume") or []
        labels = [str(x).strip() for x in row1 if str(x).strip()]
        low = [x.lower() for x in labels]
        if MANUAL_TAILOR_RESUME_COL.lower() in low:
            return
        if not labels:
            return
        new_col = len(row1) + 1
        if new_col > ws.col_count:
            self._with_retries(
                lambda: ws.resize(rows=max(ws.row_count, 100), cols=new_col),
                op_name="manual_tailor_resize_resume_col",
            )
        self._with_retries(
            lambda: ws.update_cell(1, new_col, MANUAL_TAILOR_RESUME_COL),
            op_name="manual_tailor_add_resume_col",
        )
        a1 = rowcol_to_a1(1, new_col)
        self._with_retries(
            lambda: ws.format(a1, {"textFormat": {"bold": True}}),
            op_name="manual_tailor_format_resume_header",
        )
        print(
            f"[Manual_JD_Tailor] Added final column '{MANUAL_TAILOR_RESUME_COL}' for PDF path. "
            "Older 'Tailored YAML' column (if present) is unused by the tailor script."
        )

    def read_manual_jd_tailor_urls(self, limit: int = 500) -> list[str]:
        """
        Read job-listing URLs from the Manual JD Tailor tab.

        Scans each non-empty row for an http(s) or www. URL in *any* cell (regex).
        Tries UNFORMATTED then FORMATTED values so inserted hyperlinks and plain text
        both work. Skips a header row when the first row contains a 'Job Link' column.
        """
        if not self.client:
            self.connect()
        try:
            ws = self._open_workbook().worksheet(self._manual_jd_tailor_tab_title())
        except gspread.exceptions.WorksheetNotFound:
            return []

        def _fetch_grid(vro: ValueRenderOption | None) -> list[list]:
            if vro is None:
                raw = self._with_retries(lambda: ws.get_all_values(), op_name="manual_tailor_get_all_values")
            else:
                raw = self._with_retries(
                    lambda v=vro: ws.get_all_values(value_render_option=v),
                    op_name="manual_tailor_get_all_values",
                )
            return _as_list_of_lists(raw)

        max_scanned = 0
        for vro in (ValueRenderOption.unformatted, ValueRenderOption.formatted, None):
            values = _fetch_grid(vro)
            jobs, scanned = self._parse_manual_tailor_grid_jobs(values, limit)
            max_scanned = max(max_scanned, scanned)
            if jobs:
                return [j["url"] for j in jobs]

        if max_scanned > 0:
            print(
                "[Manual_JD_Tailor] Found rows but no recognizable URLs. "
                "Paste full job posting links (https://... or www....), not only the job title.",
                file=sys.stderr,
            )
        return []

    def read_manual_jd_tailor_jobs(self, limit: int = 500) -> list[dict[str, str]]:
        """
        Rows from Manual_JD_Tailor: {"url", "recommended_resume"}.
        Optional text under header 'Recommended Resume' (any column); supply from another tool if you want.
        """
        if not self.client:
            self.connect()
        try:
            ws = self._open_workbook().worksheet(self._manual_jd_tailor_tab_title())
        except gspread.exceptions.WorksheetNotFound:
            return []

        def _fetch_grid(vro: ValueRenderOption | None) -> list[list]:
            if vro is None:
                raw = self._with_retries(lambda: ws.get_all_values(), op_name="manual_tailor_get_all_values")
            else:
                raw = self._with_retries(
                    lambda v=vro: ws.get_all_values(value_render_option=v),
                    op_name="manual_tailor_get_all_values",
                )
            return _as_list_of_lists(raw)

        for vro in (ValueRenderOption.unformatted, ValueRenderOption.formatted, None):
            values = _fetch_grid(vro)
            jobs, _ = self._parse_manual_tailor_grid_jobs(values, limit)
            if jobs:
                return jobs
        return []

    def update_manual_jd_tailor_result(
        self,
        *,
        url: str,
        status: str,
        resume_path: str = "",
        error: str = "",
        last_processed: str | None = None,
        validation_verdict: str = "",
        validation_reason: str = "",
        tailored_score: str = "",
        generic_score: str = "",
        use_resume: str = "",
    ) -> bool:
        """
        Update one Manual_JD_Tailor row by URL with status, timestamps, resume output path, and error text.
        Resume path is written to the last column (MANUAL_TAILOR_RESUME_COL), typically an absolute PDF path.
        Returns True if a matching URL row was found and updated.
        """
        if not self.client:
            self.connect()
        ws = self._open_workbook().worksheet(self._manual_jd_tailor_tab_title())
        headers = [h.strip() for h in (self._with_retries(lambda: ws.row_values(1), op_name="manual_tailor_headers") or [])]
        if not headers:
            return False

        status_col = self._get_or_create_col_index(ws, "Status", headers)
        link_col = self._get_or_create_col_index(ws, "Job Link", headers)
        last_col = self._get_or_create_col_index(ws, "Last processed", headers)
        err_col = self._get_or_create_col_index(ws, "Error", headers)
        vv_col = self._get_or_create_col_index(ws, "Validation Verdict", headers)
        vr_col = self._get_or_create_col_index(ws, "Validation Reason", headers)
        ts_col = self._get_or_create_col_index(ws, "Tailored Score", headers)
        gs_col = self._get_or_create_col_index(ws, "Generic Score", headers)
        ur_col = self._get_or_create_col_index(ws, "Use Resume", headers)
        resume_col = self._get_or_create_col_index(ws, MANUAL_TAILOR_RESUME_COL, headers)

        values = self._with_retries(lambda: ws.get_all_values(), op_name="manual_tailor_get_all_values") or []
        if len(values) <= 1:
            return False

        target = normalize_job_url(url)
        if not target:
            return False

        row_idx = -1
        for i, row in enumerate(values[1:], start=2):
            row_s = [str(c) for c in row]
            row_url = self._url_for_manual_data_row(row_s, link_col - 1)
            if normalize_job_url(row_url) == target:
                row_idx = i
                break

        if row_idx < 0:
            return False

        now = last_processed or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cells = [
            gspread.Cell(row_idx, status_col, status or ""),
            gspread.Cell(row_idx, last_col, now),
            gspread.Cell(row_idx, err_col, error or ""),
            gspread.Cell(row_idx, vv_col, validation_verdict or ""),
            gspread.Cell(row_idx, vr_col, validation_reason or ""),
            gspread.Cell(row_idx, ts_col, tailored_score or ""),
            gspread.Cell(row_idx, gs_col, generic_score or ""),
            gspread.Cell(row_idx, ur_col, use_resume or ""),
            gspread.Cell(row_idx, resume_col, resume_path or ""),
        ]
        self._with_retries(lambda: ws.update_cells(cells), op_name="manual_tailor_update_result")
        return True

    def update_manual_jd_tailor_validation_only(
        self,
        *,
        url: str,
        validation_verdict: str,
        validation_reason: str = "",
        tailored_score: str = "",
        generic_score: str = "",
        use_resume: str = "",
        last_processed: str | None = None,
    ) -> bool:
        """
        Update only validation-related columns for a Manual_JD_Tailor row (does not touch Status / Resume / Error).
        """
        if not self.client:
            self.connect()
        ws = self._open_workbook().worksheet(self._manual_jd_tailor_tab_title())
        headers = [h.strip() for h in (self._with_retries(lambda: ws.row_values(1), op_name="manual_tailor_headers_v") or [])]
        if not headers:
            return False

        link_col = self._get_or_create_col_index(ws, "Job Link", headers)
        last_col = self._get_or_create_col_index(ws, "Last processed", headers)
        vv_col = self._get_or_create_col_index(ws, "Validation Verdict", headers)
        vr_col = self._get_or_create_col_index(ws, "Validation Reason", headers)
        ts_col = self._get_or_create_col_index(ws, "Tailored Score", headers)
        gs_col = self._get_or_create_col_index(ws, "Generic Score", headers)
        ur_col = self._get_or_create_col_index(ws, "Use Resume", headers)

        values = self._with_retries(lambda: ws.get_all_values(), op_name="manual_tailor_get_all_values_v") or []
        if len(values) <= 1:
            return False

        target = normalize_job_url(url)
        if not target:
            return False

        row_idx = -1
        for i, row in enumerate(values[1:], start=2):
            row_s = [str(c) for c in row]
            row_url = self._url_for_manual_data_row(row_s, link_col - 1)
            if normalize_job_url(row_url) == target:
                row_idx = i
                break

        if row_idx < 0:
            return False

        now = last_processed or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cells = [
            gspread.Cell(row_idx, last_col, now),
            gspread.Cell(row_idx, vv_col, validation_verdict or ""),
            gspread.Cell(row_idx, vr_col, validation_reason or ""),
            gspread.Cell(row_idx, ts_col, tailored_score or ""),
            gspread.Cell(row_idx, gs_col, generic_score or ""),
            gspread.Cell(row_idx, ur_col, use_resume or ""),
        ]
        self._with_retries(lambda: ws.update_cells(cells), op_name="manual_tailor_update_validation")
        return True

    def _manual_tailor_column_indices(self, header_row: list) -> tuple[int, int]:
        h = [str(c).strip().lower() for c in header_row]

        def find(*names: str) -> int:
            for n in names:
                key = n.lower()
                try:
                    return h.index(key)
                except ValueError:
                    continue
            return -1

        jl = find("job link")
        rec = find("recommended resume", "resume variant", "eval recommended resume")
        return jl, rec

    def _url_for_manual_data_row(self, row: list[str], job_link_idx: int) -> str:
        if job_link_idx >= 0 and job_link_idx < len(row):
            u = _url_from_manual_tailor_cell(str(row[job_link_idx]))
            if u:
                return u
        return _first_job_url_in_row([str(c) for c in row])

    def _parse_manual_tailor_grid_jobs(
        self, values: list[list], limit: int
    ) -> tuple[list[dict[str, str]], int]:
        """Return (jobs with url + recommended_resume, non-empty row count scanned)."""
        if not values:
            return [], 0
        header = _manual_tailor_first_row_is_header(values[0])
        if header and len(values) < 2:
            return [], 0
        hdr = values[0]
        data_rows = values[1:] if header else values
        job_link_idx, rec_idx = (-1, -1)
        if header:
            job_link_idx, rec_idx = self._manual_tailor_column_indices(hdr)

        out: list[dict[str, str]] = []
        seen: set[str] = set()
        scanned_non_empty = 0
        for row in data_rows:
            if len(out) >= limit:
                break
            if not any(str(c).strip() for c in row):
                continue
            scanned_non_empty += 1
            row_s = [str(c) for c in row]
            link = self._url_for_manual_data_row(row_s, job_link_idx)
            if not link:
                continue
            n = normalize_job_url(link)
            if not n or n in seen:
                continue
            seen.add(n)
            rec_cell = ""
            if rec_idx >= 0 and rec_idx < len(row_s):
                rec_cell = row_s[rec_idx].strip()
            out.append({"url": link, "recommended_resume": rec_cell})
        return out, scanned_non_empty

    def _open_workbook(self):
        """Open the configured spreadsheet by ID or title. Does not create a new file."""
        if self.client is None:
            raise RuntimeError("GoogleSheetsClient.connect() required before _open_workbook()")
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
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_path, scope  # type: ignore[arg-type]
            )
            self.client = gspread.authorize(creds)  # type: ignore[arg-type]
            
            # Daily pipeline tab (YYYY-MM-DD) from config / SHEET_TAB_DATE
            tab_str = get_worksheet_tab_date()
            
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
                # Main worksheet for sourcing / evaluation
                self.sheet = spreadsheet.worksheet(tab_str)
                doc_label = getattr(spreadsheet, "title", None) or self.sheet_name
                print(f"Connected to spreadsheet '{doc_label}', tab: {tab_str}")
            except gspread.exceptions.WorksheetNotFound:
                print(f"Tab for '{tab_str}' not found. Creating it...")
                self.sheet = spreadsheet.add_worksheet(
                    title=tab_str,
                    rows=DEFAULT_NEW_WORKSHEET_ROWS,
                    cols=DEFAULT_NEW_WORKSHEET_COLS,
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
        if self.sheet is None:
            raise RuntimeError("Worksheet unavailable after connect()")
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

    def get_applied_urls(self, use_cache: bool = True):
        """Returns a set of canonical Job Links where user marked Applied? (Y/N) = Y. So we never re-add or re-evaluate those."""
        if not self.client:
            self.connect()
        if use_cache and self._cached_applied_urls is not None:
            return self._cached_applied_urls
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
        self._cached_applied_urls = applied
        return applied

    def get_already_evaluated_or_applied_canonical_urls(self, use_cache: bool = True):
        """
        Canonical URLs of jobs that are already EVALUATED or marked Applied=Y in any tab.
        Use in evaluator to skip re-evaluating so the agent and user don't process the same job again.
        """
        if not self.client:
            self.connect()
        if use_cache and self._cached_evaluated_or_applied_urls is not None:
            return self._cached_evaluated_or_applied_urls
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
        self._cached_evaluated_or_applied_urls = seen
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

    def _job_dict_for_fallback(self, job: dict) -> dict:
        out: dict = {}
        for k in _FALLBACK_JOB_KEYS:
            if k in job:
                out[k] = job[k]
        return out

    def _persist_append_fallback(self, tab_date: str, jobs: list[dict], reason: str) -> str | None:
        """Write failed-append jobs to disk for scripts/tools/replay_sheet_fallback_queue.py."""
        if os.environ.get("SHEET_APPEND_FALLBACK_JSON", "1").strip().lower() in ("0", "false", "no"):
            return None
        base = os.environ.get("SHEET_APPEND_FALLBACK_DIR", "").strip() or DEFAULT_SHEET_APPEND_FALLBACK_DIR
        try:
            os.makedirs(base, exist_ok=True)
            path = os.path.join(
                base,
                f"failed_append_{tab_date.replace('-', '')}_{datetime.now().strftime('%H%M%S')}.json",
            )
            payload = {"tab_date": tab_date, "reason": reason[:2000], "jobs": jobs}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            print(f"[Sheets fallback] wrote {path}")
            return path
        except OSError as e:
            print(f"[Sheets fallback] Could not write: {e}")
            return None

    def add_jobs(self, jobs_list):
        """
        Adds new jobs. Skips duplicates; updates jd_cache before append so JD survives append failures.
        On Sheets errors after building rows, persists fallback JSON and enqueues SQLite outbox when enabled.
        """
        tab_date = get_worksheet_tab_date()
        pending_jobs: list[dict] = []
        try:
            if not self.sheet:
                self.connect()

            existing = self.get_existing_urls() or set()
            applied = self.get_applied_urls() or set()
            seen = set(existing) | set(applied)

            new_rows = []
            jd_cache_updates = {}
            pending_verified = 0
            pending_unverified = 0
            for job in jobs_list or []:
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
                        "timestamp": datetime.now().strftime("%Y-%m-%d"),
                    }

                row = [""] * 17
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
                if jd_verified:
                    pending_verified += 1
                else:
                    pending_unverified += 1
                pending_jobs.append(self._job_dict_for_fallback(job))
                seen.add(canonical)

            if not new_rows:
                if jobs_list:
                    print("No new jobs to add (all duplicates or empty).")
                else:
                    print("No new jobs to add.")
                return

            if not self.sheet:
                self.connect()
            worksheet = self.sheet
            if worksheet is None:
                raise RuntimeError("Worksheet unavailable; cannot append rows.")
            logger.info(
                "add_jobs: appending %s rows (jd_verified=Y: %s, jd_verified=N/NO_JD: %s) on tab_date=%s",
                len(new_rows),
                pending_verified,
                pending_unverified,
                tab_date,
            )
            if jd_cache_updates:
                cache = self._load_jd_cache()
                cache.update(jd_cache_updates)
                self._save_jd_cache(cache)

            to_save = pending_jobs
            self._with_retries(lambda: worksheet.append_rows(new_rows), op_name="append_rows")
            self._cached_existing_urls = seen
            print(f"Added {len(new_rows)} new jobs.")
        except Exception as e:
            to_save = pending_jobs if pending_jobs else [self._job_dict_for_fallback(j) for j in (jobs_list or [])]
            if to_save:
                self._persist_append_fallback(tab_date, to_save, str(e))
                sheet_outbox.enqueue_outbox("add_jobs", tab_date, {"jobs": to_save}, str(e))
            raise

    def count_evaluated_jobs_min_score(self, min_score: float = 80.0) -> int:
        """Count rows on the active daily tab where Status=EVALUATED and Apply Score >= min_score."""
        if not self.client:
            self.connect()
        tab_date_str = get_worksheet_tab_date()

        def _read_records():
            worksheet = self._open_workbook().worksheet(tab_date_str)
            return worksheet.get_all_records()

        try:
            records = self._with_retries(_read_records, op_name="count_evaluated_records")
        except Exception as e:
            raise SheetsReadError(str(e)) from e

        n = 0
        for r in records or []:
            if str(r.get("Status", "")).strip().upper() != "EVALUATED":
                continue
            try:
                s = float(str(r.get("Apply Score", "0") or "0").strip())
            except ValueError:
                s = 0.0
            if s >= float(min_score):
                n += 1
        return n

    def get_new_jobs(self, limit=100):
        """Fetches up to `limit` jobs that have the 'NEW' status from today's tab."""
        return self._get_jobs_by_criteria({"Status": "NEW"}, limit)

    def get_needs_review_jobs(self, limit=100):
        """Jobs with Status NEEDS_REVIEW on the active daily tab (parse/LLM recovery)."""
        return self._get_jobs_by_criteria({"Status": "NEEDS_REVIEW"}, limit)

    def get_llm_failed_jobs(self, limit=100):
        """Jobs with Status LLM_FAILED on the active daily tab."""
        return self._get_jobs_by_criteria({"Status": "LLM_FAILED"}, limit)

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
        """Internal helper to fetch jobs based on column-value criteria (active daily tab)."""
        if not self.client:
            self.connect()

        tab_str = get_worksheet_tab_date()
        try:
            worksheet = self._open_workbook().worksheet(tab_str)
            records = self._with_retries(
                lambda: worksheet.get_all_records(),
                op_name="get_all_records",
            ) or []

            filtered_jobs = []
            for i, record in enumerate(records):
                match = True
                for key, val in criteria.items():
                    actual = str(record.get(key, "")).strip()
                    target = str(val).strip()

                    if key == "Match Type":
                        actual = actual.replace("*", "")

                    if actual.lower() != target.lower():
                        match = False
                        break

                if match:
                    record["_row_index"] = i + 2
                    record["_worksheet"] = worksheet
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
            cells_to_update.append(gspread.Cell(row=row_index, col=match_col, value=str(match_type)))
            cells_to_update.append(gspread.Cell(row=row_index, col=score_col, value=str(score)))
            cells_to_update.append(gspread.Cell(row=row_index, col=resume_col, value=recommended))
            cells_to_update.append(gspread.Cell(row=row_index, col=h1b_col, value=h1b))
            cells_to_update.append(gspread.Cell(row=row_index, col=reason_col, value=final_reason))
            cells_to_update.append(gspread.Cell(row=row_index, col=skills_col, value=missing))
            cells_to_update.append(
                gspread.Cell(row=row_index, col=cal_col, value=str(u["calibration_delta"]))
            )
            cells_to_update.append(gspread.Cell(row=row_index, col=audit_col, value=u["decision_audit_json"]))
            cells_to_update.append(gspread.Cell(row=row_index, col=ev_col, value=u.get("evidence_json") or ""))
            base_raw = u["base_llm_score"]
            if base_raw is None or base_raw == "":
                base_out = ""
            else:
                base_out = str(int(base_raw))
            cells_to_update.append(gspread.Cell(row=row_index, col=base_col, value=base_out))
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
            rj_out = "" if rj_score_int == "" else str(rj_score_int)
            cells_to_update.append(gspread.Cell(row=row_index, col=rj_score_col, value=rj_out))
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
            ats_out = "" if ats_pct_int == "" else str(ats_pct_int)
            cells_to_update.append(gspread.Cell(row=row_index, col=ats_match_col, value=ats_out))
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
            
        tab_str = get_worksheet_tab_date()
        try:
            worksheet = self._open_workbook().worksheet(tab_str)
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

    def _with_retries(self, fn, op_name="operation", retries=None, base_sleep=None, **kwargs):
        """
        Retry wrapper for transient Sheets API failures.
        Env: SHEETS_RETRY_MAX, SHEETS_BASE_SLEEP, SHEETS_MIN_REQUEST_INTERVAL_SEC (pacing between calls).
        Raises SheetsReadError on persistent quota (429) after retries.
        """
        if kwargs:
            pass  # forward-compatibility for call sites
        if retries is None:
            retries = int(os.environ.get("SHEETS_RETRY_MAX", "3") or "3")
        if base_sleep is None:
            base_sleep = float(os.environ.get("SHEETS_BASE_SLEEP", "1.5") or "1.5")
        min_interval = float(os.environ.get("SHEETS_MIN_REQUEST_INTERVAL_SEC", "0") or "0")

        last_error = None
        for attempt in range(1, max(1, retries) + 1):
            if min_interval > 0:
                last_end = getattr(self, "_last_sheets_call_end_monotonic", 0.0) or 0.0
                if last_end > 0:
                    elapsed = time.monotonic() - last_end
                    if elapsed < min_interval:
                        time.sleep(min_interval - elapsed)
            try:
                out = fn()
                self._last_sheets_call_end_monotonic = time.monotonic()
                return out
            except Exception as e:
                last_error = e
                is_quota = False
                if isinstance(e, APIError):
                    try:
                        if getattr(e.response, "status_code", None) == 429:
                            is_quota = True
                    except Exception:
                        pass
                low = str(e).lower()
                if "429" in low or "quota" in low:
                    is_quota = True
                if attempt >= retries:
                    if is_quota:
                        raise SheetsReadError(str(e)) from e
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
