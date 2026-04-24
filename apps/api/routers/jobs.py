"""
Read job rows from Google Sheets (daily tab) for the ops dashboard.

Requires config/credentials.json and sheet id like the CLI (run from repo root).
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Query

# Repo root on path for apps.cli imports
from apps.api.paths import PROJECT_ROOT

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient, normalize_job_url

router = APIRouter()


def _sheet_rows(worksheet) -> List[Dict[str, Any]]:
    values = worksheet.get_all_values()
    if len(values) < 2:
        return []
    headers = [str(c).strip() for c in values[0]]
    out: List[Dict[str, Any]] = []
    for ri, row in enumerate(values[1:], start=2):
        rec: Dict[str, Any] = {"_row_index": ri}
        for ci, h in enumerate(headers):
            cell = row[ci] if ci < len(row) else ""
            rec[h] = cell
        out.append(rec)
    return out


def _parse_score(raw: Any) -> Optional[int]:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def _open_tab(client: GoogleSheetsClient, tab_date: str):
    if not client.client:
        client.connect()
    ws = client._open_workbook().worksheet(tab_date)
    return ws


@router.get("/jobs")
def list_jobs(
    tab: Optional[str] = Query(
        None,
        description="Worksheet tab YYYY-MM-DD. Default: same logic as CLI (today/yesterday per config).",
    ),
    min_score: int = Query(0, ge=0, le=100),
    limit: int = Query(200, ge=1, le=500),
    must_apply_only: bool = Query(False, description="If true, filter rows that look like top tiers"),
    has_resume: bool = Query(False, description="If true, only rows with a non-empty Resume Path"),
) -> Dict[str, Any]:
    """List job rows from the daily sheet with scores and resume fields."""
    tab_date = (tab or "").strip()
    if tab_date:
        os.environ["SHEET_TAB_DATE"] = tab_date[:10]
    rows: List[Dict[str, Any]] = []
    active_tab = ""
    try:
        client = GoogleSheetsClient()
        client.connect()
        from apps.cli.legacy.core.config import get_worksheet_tab_date

        active_tab = get_worksheet_tab_date()
        ws = _open_tab(client, active_tab)
        rows = _sheet_rows(ws)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Sheets unavailable: {e!s}. Run API from repo root with config/credentials.json.",
        ) from e
    finally:
        if tab_date:
            os.environ.pop("SHEET_TAB_DATE", None)

    compact: List[Dict[str, Any]] = []
    for r in rows:
        score = _parse_score(r.get("Apply Score"))
        if score is not None and score < min_score:
            continue
        mt = str(r.get("Match Type") or "")
        if must_apply_only:
            if "Must" not in mt and "Strong" not in mt and (score is None or score < 85):
                continue
        if has_resume and not str(r.get("Resume Path") or "").strip():
            continue
        reasoning = str(r.get("Reasoning") or "")
        compact.append(
            {
                "row_index": r.get("_row_index"),
                "status": str(r.get("Status") or ""),
                "role_title": str(r.get("Role Title") or ""),
                "company": str(r.get("Company") or ""),
                "location": str(r.get("Location") or ""),
                "job_link": str(r.get("Job Link") or ""),
                "source": str(r.get("Source") or ""),
                "apply_score": score,
                "match_type": mt,
                "recommended_resume": str(r.get("Recommended Resume") or ""),
                "h1b_sponsorship": str(r.get("H1B Sponsorship") or ""),
                "resume_status": str(r.get("Resume Status") or ""),
                "resume_path": str(r.get("Resume Path") or ""),
                "apply_bucket": str(r.get("Apply Bucket") or ""),
                "reasoning_preview": reasoning[:280] + ("…" if len(reasoning) > 280 else ""),
            }
        )
        if len(compact) >= limit:
            break

    return {"tab": active_tab, "count": len(compact), "jobs": compact}


@router.get("/jobs/detail")
def job_detail(
    url: str = Query(..., description="Job posting URL (exact or normalized; will be normalized)"),
) -> Dict[str, Any]:
    """Return one row's fields including Evidence JSON (full text may be large)."""
    target = normalize_job_url(unquote(url))
    if not target:
        raise HTTPException(status_code=400, detail="Invalid url")
    try:
        client = GoogleSheetsClient()
        client.connect()
        from apps.cli.legacy.core.config import get_worksheet_tab_date

        active_tab = get_worksheet_tab_date()
        ws = _open_tab(client, active_tab)
        rows = _sheet_rows(ws)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Sheets unavailable: {e!s}") from e

    for r in rows:
        link = normalize_job_url(str(r.get("Job Link") or ""))
        if link == target:
            return {"tab": active_tab, "job": r}
    raise HTTPException(status_code=404, detail="Job URL not found on today's tab")


@router.get("/meta/sheet")
def sheet_meta() -> Dict[str, Any]:
    """Current resolved tab date and spreadsheet id hint (no secrets)."""
    from apps.cli.legacy.core.config import get_worksheet_tab_date, get_sheet_config

    sc = get_sheet_config()
    sid = str(sc.get("spreadsheet_id") or os.environ.get("GOOGLE_SHEET_ID") or "")
    preview = sid[:12] + "…" if len(sid) > 20 else sid
    return {
        "worksheet_tab": get_worksheet_tab_date(),
        "spreadsheet_id_preview": preview,
        "project_root": PROJECT_ROOT,
    }
