#!/usr/bin/env python3
"""
Normalize Status column (A) on a tab to NEW / EVALUATED / NO_JD / etc. (uppercase).

Dry-run by default. Use --apply to write changes.

Usage:
  python3 scripts/diagnostics/normalize_sheet_statuses.py
  python3 scripts/diagnostics/normalize_sheet_statuses.py --apply --date 2026-04-09
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import gspread

from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient

# Target values we normalize toward (first match wins)
_CANON = {
    "new": "NEW",
    "evaluated": "EVALUATED",
    "no_jd": "NO_JD",
    "no jd": "NO_JD",
    "skipped": "SKIPPED",
}


def _normalize_status(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    key = s.lower().replace(" ", "_")
    if key in _CANON:
        return _CANON[key]
    if s.isupper() and s in ("NEW", "EVALUATED", "NO_JD", "SKIPPED"):
        return s
    # Title-case single word
    if s.lower() in ("new", "evaluated", "skipped"):
        return s.upper()
    return s


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="", help="Tab YYYY-MM-DD (default: today)")
    parser.add_argument("--apply", action="store_true", help="Write changes (default dry-run)")
    args = parser.parse_args()
    tab = (args.date or "").strip() or datetime.now().strftime("%Y-%m-%d")

    client = GoogleSheetsClient()
    client.connect()
    spreadsheet = client._open_workbook()
    ws = spreadsheet.worksheet(tab)
    values = ws.get_all_values()
    if len(values) < 2:
        print("No data rows.")
        return 0

    updates: list[gspread.Cell] = []
    for i, row in enumerate(values[1:], start=2):
        if not row:
            continue
        cur = row[0] if len(row) > 0 else ""
        nxt = _normalize_status(cur)
        if nxt and nxt != cur:
            updates.append(gspread.Cell(row=i, col=1, value=nxt))
            print(f"row {i}: {cur!r} -> {nxt!r}")

    if not updates:
        print("No status cells need normalization.")
        return 0

    if args.apply:
        client._with_retries(lambda: ws.update_cells(updates), op_name="normalize_statuses")
        print(f"Applied {len(updates)} updates.")
    else:
        print(f"Dry-run: {len(updates)} cells would change. Re-run with --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
