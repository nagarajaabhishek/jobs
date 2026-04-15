#!/usr/bin/env python3
"""
Print sourcing / sheet backlog diagnostics for the configured daily tab (or --date).

Usage (repo root):
  python3 scripts/diagnostics/sheet_sourcing_health.py
  python3 scripts/diagnostics/sheet_sourcing_health.py --date 2026-04-14
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.core.config import get_worksheet_tab_date  # noqa: E402
from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient  # noqa: E402


def _jd_cache_stats(path: str) -> tuple[int, bool]:
    import json

    if not os.path.isfile(path):
        return 0, False
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return (len(data) if isinstance(data, dict) else 0, True)
    except OSError:
        return 0, False


def main() -> int:
    ap = argparse.ArgumentParser(description="Sheet status counts + JD cache / outbox hints.")
    ap.add_argument("--date", default="", help="Tab YYYY-MM-DD (default: active worksheet per config/env)")
    args = ap.parse_args()

    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
    except ImportError:
        pass

    tab = (args.date or "").strip() or get_worksheet_tab_date()
    print(f"Worksheet tab (resolved): {tab}")
    print(f"SHEET_TAB_DATE env: {(os.environ.get('SHEET_TAB_DATE') or '').strip() or '(unset)'}")

    jd_path = os.path.join(PROJECT_ROOT, "config", "jd_cache.json")
    n_cached, exists = _jd_cache_stats(jd_path)
    print(f"JD cache ({jd_path}): {'present' if exists else 'missing'}, {n_cached} URL(s)")

    outbox_db = os.path.join(PROJECT_ROOT, "data", "pipeline_outbox.db")
    print(f"Outbox DB ({outbox_db}): {'exists' if os.path.isfile(outbox_db) else 'missing'}")
    fallback_dir = os.path.join(PROJECT_ROOT, "data", "sheet_append_fallback")
    if os.path.isdir(fallback_dir):
        n_fallback = len([x for x in os.listdir(fallback_dir) if not x.startswith(".")])
        print(f"Sheet append fallback dir: {n_fallback} file(s)")
    else:
        print("Sheet append fallback dir: (none)")

    client = GoogleSheetsClient()
    client.connect()
    wb = client._open_workbook()
    try:
        ws = wb.worksheet(tab)
    except Exception as e:
        print(f"ERROR: could not open tab {tab!r}: {e}")
        return 1

    records = ws.get_all_records()
    if not records:
        print(f"Tab {tab}: 0 data rows (empty or header only).")
        return 0

    status_col = "Status"
    c: Counter[str] = Counter()
    for r in records:
        s = str(r.get(status_col, "") or "").strip() or "(blank)"
        c[s] += 1

    print(f"\nTab {tab}: {len(records)} row(s) (excluding header)")
    print("Status distribution:")
    for k, v in c.most_common():
        print(f"  {k}: {v}")

    no_jd = c.get("NO_JD", 0)
    new_n = c.get("NEW", 0)
    if no_jd and new_n == 0:
        print(
            "\nNote: NO_JD rows are not picked up by evaluate_all(NEW). "
            "Improve JD fetch or fix listings before evaluation runs."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
