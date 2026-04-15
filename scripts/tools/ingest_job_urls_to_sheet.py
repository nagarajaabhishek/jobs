#!/usr/bin/env python3
"""
Append job rows to the Google Sheet daily tab by fetching JD text for each URL.
Writes jd_cache first (same as pipeline sourcing). Rows get Status=NEW when JD is verified.

Does not run JobEvaluator. Use the main pipeline or evaluate_jobs for scoring.

Usage (repo root):
  python3 scripts/tools/ingest_job_urls_to_sheet.py "https://..." "https://..."
  python3 scripts/tools/ingest_job_urls_to_sheet.py --file urls.txt
  # Pull URLs from the Manual_JD_Tailor tab (paste links in Job Link column; create tab first with --ensure-tailor-tab)
  python3 scripts/tools/ingest_job_urls_to_sheet.py --from-tailor-tab --ensure-tailor-tab
  SHEET_TAB_DATE=2026-04-14 python3 scripts/tools/ingest_job_urls_to_sheet.py --file urls.txt
"""
from __future__ import annotations

import argparse
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient  # noqa: E402
from apps.cli.legacy.core.jd_cache_helpers import ensure_jd_cached  # noqa: E402


def _read_urls(file_opt: str | None, extra: list[str]) -> list[str]:
    raw: list[str] = []
    if file_opt:
        with open(file_opt, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    raw.append(line)
    raw.extend(extra)
    seen = set()
    out: list[str] = []
    for u in raw:
        u = u.strip()
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def _job_dict_from_url(client: GoogleSheetsClient, url: str) -> dict:
    """Build a job dict compatible with add_jobs after JD fetch."""
    ok, jd_msg = ensure_jd_cached(client, url, project_root=PROJECT_ROOT)
    desc = (client.get_jd_for_url(url) or "").strip()
    jd_verified = bool(ok and desc and len(desc) >= 200 and desc.lower() != "none")
    return {
        "title": "Manual URL import",
        "company": "",
        "url": url,
        "location": "United States",
        "source": "manual_ingest",
        "site": "manual_ingest",
        "description": desc,
        "jd_verified": jd_verified,
        "jd_fetch_method": "manual_ingest",
        "jd_fetch_reason": "" if jd_verified else f"short_or_unfetched:{jd_msg}",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest URLs into sheet + jd_cache (no LLM eval).")
    ap.add_argument("urls", nargs="*", help="Job posting URLs")
    ap.add_argument("--file", "-f", help="One URL per line (# comments ok)")
    ap.add_argument(
        "--tab",
        default="",
        help="Tab YYYY-MM-DD to append to: sets SHEET_TAB_DATE for this process (default: config-driven)",
    )
    ap.add_argument(
        "--from-tailor-tab",
        action="store_true",
        help="Read job URLs from the Manual_JD_Tailor worksheet (Job Link column).",
    )
    ap.add_argument(
        "--ensure-tailor-tab",
        action="store_true",
        help="Create the Manual_JD_Tailor tab (with headers) if it does not exist.",
    )
    args = ap.parse_args()

    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
    except ImportError:
        pass

    if args.tab.strip():
        os.environ["SHEET_TAB_DATE"] = args.tab.strip()[:10]

    client = GoogleSheetsClient()
    client.connect()
    if args.ensure_tailor_tab:
        client.ensure_manual_jd_tailor_worksheet()

    if args.from_tailor_tab:
        urls = client.read_manual_jd_tailor_urls()
        if not urls:
            print("No URLs found on Manual_JD_Tailor tab (Job Link column).", file=sys.stderr)
            return 2
    else:
        urls = _read_urls(args.file, list(args.urls))
        if not urls:
            print("No URLs.", file=sys.stderr)
            return 2

    jobs = [_job_dict_from_url(client, url) for url in urls]

    client.add_jobs(jobs)
    print(f"Processed {len(jobs)} URL(s); duplicates skipped by add_jobs. Tab date: {os.environ.get('SHEET_TAB_DATE', '') or '(config default)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
