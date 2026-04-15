#!/usr/bin/env python3
"""
Replay jobs saved when Google Sheets append (or pre-append reads) failed.

Each file under data/sheet_append_fallback/ is JSON:
  {"tab_date": "YYYY-MM-DD", "reason": "...", "jobs": [ {...}, ... ]}

Run from repo root with credentials and GOOGLE_SHEET_ID (or pipeline config) set.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    ap = argparse.ArgumentParser(description="Replay sheet append fallback batches to Google Sheets.")
    ap.add_argument(
        "--dir",
        default=os.environ.get("SHEET_APPEND_FALLBACK_DIR") or str(_repo_root() / "data" / "sheet_append_fallback"),
        help="Directory containing failed_*.json files",
    )
    ap.add_argument("--dry-run", action="store_true", help="List batches only; do not call Sheets.")
    ap.add_argument("--move-on-success", action="store_true", help="Move replayed file to replayed/ under the same dir.")
    args = ap.parse_args()

    base = Path(args.dir)
    if not base.is_dir():
        print(f"Directory not found: {base}", file=sys.stderr)
        return 1

    files = sorted(base.glob("failed_*.json"), key=lambda p: p.stat().st_mtime)
    if not files:
        print(f"No failed_*.json files in {base}")
        return 0

    repo = _repo_root()
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))

    try:
        from dotenv import load_dotenv

        load_dotenv(repo / ".env")
    except ImportError:
        pass

    from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient

    for path in files:
        with open(path, encoding="utf-8") as f:
            record = json.load(f)
        tab_date = str(record.get("tab_date") or "").strip()[:10]
        jobs = record.get("jobs") or []
        if not tab_date or not jobs:
            print(f"Skip (missing tab_date or jobs): {path}")
            continue
        print(f"\n--- {path.name} tab={tab_date} jobs={len(jobs)} reason={str(record.get('reason', ''))[:100]!r}")
        if args.dry_run:
            continue
        os.environ["SHEET_TAB_DATE"] = tab_date
        client = GoogleSheetsClient()
        client.connect()
        try:
            client.add_jobs(jobs)
        except Exception as e:
            print(f"Replay failed for {path}: {e}", file=sys.stderr)
            return 1
        if args.move_on_success:
            done = base / "replayed"
            done.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(done / path.name))
            print(f"Moved to {done / path.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
