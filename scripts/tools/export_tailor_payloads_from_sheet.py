#!/usr/bin/env python3
"""
Backfill data/tailor_payloads/*.json from the current sheet (no re-LLM).
Uses Apply Score >= min_score or Apply Bucket MUST_APPLY. JD text from local jd_cache.

Usage (repo root):
  python3 scripts/tools/export_tailor_payloads_from_sheet.py --min-score 90
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient, normalize_job_url


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--date", default="", help="Tab YYYY-MM-DD (default: today)")
    p.add_argument("--min-score", type=int, default=90)
    args = p.parse_args()
    tab = (args.date or "").strip() or datetime.now().strftime("%Y-%m-%d")

    client = GoogleSheetsClient()
    client.connect()
    spreadsheet = client._open_workbook()
    ws = spreadsheet.worksheet(tab)
    records = ws.get_all_records()

    out_dir = os.path.join(PROJECT_ROOT, "data", "tailor_payloads")
    os.makedirs(out_dir, exist_ok=True)

    written = 0
    for i, rec in enumerate(records):
        try:
            score = int(str(rec.get("Apply Score", "0")).strip())
        except ValueError:
            score = 0
        bucket = str(rec.get("Apply Bucket", "") or "").strip().upper()
        if score < args.min_score and bucket != "MUST_APPLY":
            continue

        link = rec.get("Job Link") or ""
        jd = (client.get_jd_for_url(link) or "").strip()
        if not jd:
            print(f"skip row {i+2}: no JD in cache for link")
            continue

        gaps_raw = str(rec.get("Missing Skills", "") or "")
        gaps = [s.strip() for s in gaps_raw.split(",") if s.strip()]

        payload = {
            "exported_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "source": "export_tailor_payloads_from_sheet.py",
            "row_index": i + 2,
            "job_link": link,
            "canonical_url": normalize_job_url(link),
            "company": rec.get("Company"),
            "role_title": rec.get("Role Title"),
            "apply_conviction_score": score,
            "apply_bucket": bucket,
            "recommended_resume": rec.get("Recommended Resume"),
            "skill_gaps": gaps,
            "jd_excerpt": jd[:12000],
            "reasoning_excerpt": str(rec.get("Reasoning", "") or "")[:4000],
            "notes": "Backfilled from sheet; verify before tailoring PDF/LaTeX.",
        }

        fname = f"{tab}_row{i+2}.json"
        path = os.path.join(out_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        written += 1
        print(path)

    print(f"Wrote {written} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
