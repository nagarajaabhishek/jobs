#!/usr/bin/env python3
"""
Build a daily digest (JSON + Markdown) of top evaluated jobs with explainability.

Optionally updates Google Sheet columns Digest Status and Action Link for included rows.

Run from project root:
  python3 apps/cli/scripts/tools/build_job_digest.py
  python3 apps/cli/scripts/tools/build_job_digest.py --top 15 --update-sheet
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.core.config import get_digest_config
from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient, normalize_job_url
from apps.cli.legacy.core.learning_schemas import SHEET_COL_ACTION_LINK, SHEET_COL_DIGEST_STATUS, DecisionAudit


def _score_int(row: Dict[str, Any]) -> int:
    try:
        return int(str(row.get("Apply Score", "0")).strip())
    except ValueError:
        return 0


def build_digest(top_n: int, update_sheet: bool, dry_run: bool) -> str:
    os.chdir(PROJECT_ROOT)
    cfg = get_digest_config()
    n = int(top_n or cfg.get("top_n", 20))
    out_dir = cfg.get("output_dir", "data/digests")
    out_abs = out_dir if os.path.isabs(out_dir) else os.path.join(PROJECT_ROOT, out_dir)
    os.makedirs(out_abs, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    client = GoogleSheetsClient()
    client.connect()
    ws = client.client.open(client.sheet_name).worksheet(today)
    records = ws.get_all_records()
    if not records:
        print("No records for today.")
        return ""

    # Evaluated rows only
    rows = [r for r in records if str(r.get("Status", "")).strip().upper() == "EVALUATED"]
    rows.sort(key=_score_int, reverse=True)
    top = rows[:n]

    digest_jobs: List[Dict[str, Any]] = []
    for r in top:
        audit_raw = str(r.get("Decision Audit JSON", "") or "")
        why = ""
        try:
            audit = DecisionAudit.from_json(audit_raw)
            if audit.matched_patterns:
                why = "; ".join(
                    f"{m.get('pattern_type')}:{m.get('pattern_value')} ({m.get('contribution')})"
                    for m in audit.matched_patterns
                )
        except Exception:
            pass
        digest_jobs.append(
            {
                "role_title": r.get("Role Title", ""),
                "company": r.get("Company", ""),
                "location": r.get("Location", ""),
                "apply_score": _score_int(r),
                "match_type": r.get("Match Type", ""),
                "job_link": r.get("Job Link", ""),
                "reasoning": r.get("Reasoning", ""),
                "h1b": r.get("H1B Sponsorship", ""),
                "recommended_resume": r.get("Recommended Resume", ""),
                "calibration_delta": r.get("Calibration Delta", ""),
                "audit_patterns": why,
            }
        )

    payload = {
        "date": today,
        "top_n": n,
        "jobs": digest_jobs,
    }

    json_path = os.path.join(out_abs, f"{today}_digest.json")
    md_path = os.path.join(out_abs, f"{today}_digest.md")

    if not dry_run:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        lines = [f"# Job digest {today}", ""]
        for j in digest_jobs:
            lines.append(f"## {j['role_title']} @ {j['company']} ({j['location']})")
            lines.append(f"- Score: **{j['apply_score']}** | {j['match_type']}")
            lines.append(f"- Apply: {j['job_link']}")
            if j.get("audit_patterns"):
                lines.append(f"- Calibration: {j['audit_patterns']}")
            lines.append(f"- Why: {j['reasoning'][:500]}{'...' if len(str(j['reasoning'])) > 500 else ''}")
            lines.append("")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    print(f"Wrote {json_path} and {md_path} ({len(digest_jobs)} jobs)")

    if update_sheet and not dry_run:
        headers = [h.strip() for h in ws.row_values(1)]
        # Build row index map from get_all_values for reliable indices
        values = ws.get_all_values()
        headers = [h.strip() for h in values[0]]
        link_idx = headers.index("Job Link") if "Job Link" in headers else -1
        dig_idx = client._get_or_create_col_index(ws, SHEET_COL_DIGEST_STATUS, headers)
        act_idx = client._get_or_create_col_index(ws, SHEET_COL_ACTION_LINK, headers)

        cells = []
        top_links = {normalize_job_url(str(j["job_link"])) for j in digest_jobs if j.get("job_link")}
        for ri, row in enumerate(values[1:], start=2):
            while len(row) < len(headers):
                row.append("")
            if link_idx < 0:
                break
            link = normalize_job_url(str(row[link_idx]).strip())
            if link in top_links:
                cells.append((ri, dig_idx, "included"))
                cells.append((ri, act_idx, link))
        if cells:
            from gspread import Cell

            client._with_retries(
                lambda: ws.update_cells([Cell(row=r, col=c, value=v) for r, c, v in cells]),
                op_name="digest_update_cells",
            )
            print(f"Updated Digest Status / Action Link for {len(cells)//2} rows.")

    return json_path


def main():
    ap = argparse.ArgumentParser(description="Build daily job digest")
    ap.add_argument("--top", type=int, default=0, help="Override top N")
    ap.add_argument("--update-sheet", action="store_true", help="Mark digest rows in sheet")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    build_digest(top_n=args.top or 0, update_sheet=args.update_sheet, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
