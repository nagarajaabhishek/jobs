#!/usr/bin/env python3
"""
Export today's Google Sheet tab to TSV under data/exports/ for external viewers
(e.g. career-ops Go dashboard in a separate clone — point it at this file).

Usage (repo root):
  python3 scripts/tools/export_sheet_for_career_ops_tui.py
  python3 scripts/tools/export_sheet_for_career_ops_tui.py --date 2026-04-09
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from datetime import datetime

from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient


def main() -> int:
    parser = argparse.ArgumentParser(description="Export sheet tab to TSV.")
    parser.add_argument(
        "--date",
        default="",
        help="Worksheet tab name (YYYY-MM-DD). Default: today.",
    )
    args = parser.parse_args()
    tab = (args.date or "").strip() or datetime.now().strftime("%Y-%m-%d")

    out_dir = os.path.join(PROJECT_ROOT, "data", "exports")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"sheet_export_{tab}.tsv")

    client = GoogleSheetsClient()
    client.connect()
    spreadsheet = client._open_workbook()
    ws = spreadsheet.worksheet(tab)
    values = ws.get_all_values()

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
        for row in values:
            w.writerow(row)

    print(f"Wrote {len(values)} rows to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
