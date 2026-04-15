#!/usr/bin/env python3
"""
List duplicate Job Link rows (canonical URL) on a sheet tab. Read-only.

Usage (repo root):
  python3 scripts/diagnostics/dedup_sheet_urls.py
  python3 scripts/diagnostics/dedup_sheet_urls.py --date 2026-04-09
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient, normalize_job_url


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="", help="Tab YYYY-MM-DD (default: today)")
    args = parser.parse_args()
    tab = (args.date or "").strip() or datetime.now().strftime("%Y-%m-%d")

    client = GoogleSheetsClient()
    client.connect()
    spreadsheet = client._open_workbook()
    ws = spreadsheet.worksheet(tab)
    records = ws.get_all_records()

    by_url: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    for i, rec in enumerate(records):
        url = normalize_job_url(rec.get("Job Link") or "")
        if not url:
            continue
        row_1based = i + 2
        title = str(rec.get("Role Title") or "")
        company = str(rec.get("Company") or "")
        by_url[url].append((row_1based, title, company))

    dupes = {u: rows for u, rows in by_url.items() if len(rows) > 1}
    if not dupes:
        print(f"No duplicate canonical URLs on tab {tab}.")
        return 0

    print(f"Duplicate URLs on {tab} ({len(dupes)} canonical keys):\n")
    for url, rows in sorted(dupes.items(), key=lambda x: -len(x[1])):
        print(url)
        for row_ix, title, company in rows:
            print(f"  row {row_ix}: {company!r} — {title!r}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
