#!/usr/bin/env python3
"""
Replay pending rows from the SQLite sheet_outbox (failed Google Sheets writes).

For op_type update_eval, replay assumes row indices on the tab still match the sheet
at failure time; sorting or manual edits before replay can mis-apply cells.

Usage (from repo root, credentials configured):
  python scripts/tools/sync_sheet_outbox.py --dry-run
  python scripts/tools/sync_sheet_outbox.py --limit 20
  python scripts/tools/sync_sheet_outbox.py --also-json-dir data/sheet_append_fallback

Optional legacy JSON batches (same format as replay_sheet_fallback_queue.py) run after SQLite.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _replay_json_dir(client, base: Path, dry_run: bool, move_on_success: bool) -> int:
    """Replay failed_*.json from directory; returns count failed (non-zero exit if any)."""
    if not base.is_dir():
        return 0
    files = sorted(base.glob("failed_*.json"), key=lambda p: p.stat().st_mtime)
    failed = 0
    for path in files:
        with open(path, encoding="utf-8") as f:
            record = json.load(f)
        tab_date = str(record.get("tab_date") or "").strip()[:10]
        jobs = record.get("jobs") or []
        if not tab_date or not jobs:
            print(f"[json] Skip {path.name}")
            continue
        print(f"\n[json] {path.name} tab={tab_date} jobs={len(jobs)}")
        if dry_run:
            continue
        os.environ["SHEET_TAB_DATE"] = tab_date
        client.connect()
        try:
            client.add_jobs(jobs)
        except Exception as e:
            print(f"[json] Replay failed {path}: {e}", file=sys.stderr)
            failed += 1
            continue
        if move_on_success:
            import shutil

            done = base / "replayed"
            done.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(done / path.name))
            print(f"[json] Moved to {done / path.name}")
    return failed


def main() -> int:
    ap = argparse.ArgumentParser(description="Replay SQLite sheet_outbox pending rows to Google Sheets.")
    ap.add_argument("--db", default="", help="Override PIPELINE_OUTBOX_DB / default from config")
    ap.add_argument("--dry-run", action="store_true", help="Print pending rows only")
    ap.add_argument("--limit", type=int, default=100, help="Max pending outbox rows to process")
    ap.add_argument(
        "--mark-dead-on-error",
        action="store_true",
        help="Mark outbox row dead after replay failure; default leaves pending for retry",
    )
    ap.add_argument(
        "--also-json-dir",
        default="",
        help="After SQLite, replay legacy failed_*.json from this directory (e.g. data/sheet_append_fallback)",
    )
    ap.add_argument(
        "--json-move-on-success",
        action="store_true",
        help="With --also-json-dir, move replayed JSON files to replayed/ under that dir",
    )
    args = ap.parse_args()

    repo = _repo_root()
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))

    try:
        from dotenv import load_dotenv

        load_dotenv(repo / ".env")
    except ImportError:
        pass

    if args.db.strip():
        os.environ["PIPELINE_OUTBOX_DB"] = args.db.strip()

    from apps.cli.legacy.core import sheet_outbox
    from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient

    db_path = sheet_outbox.resolve_outbox_db_path()
    pending = sheet_outbox.list_pending(limit=args.limit, db_path=db_path)
    if not pending:
        print(f"No pending outbox rows in {db_path}")
    any_fail = False
    for row in pending:
        rid = row["id"]
        op = row["op_type"]
        tab = str(row["tab_date"] or "").strip()[:10]
        print(f"\n[outbox] id={rid} op={op} tab={tab} created={row.get('created_at')}")
        if args.dry_run:
            continue
        client = GoogleSheetsClient()
        try:
            payload = json.loads(row["payload_json"])
            if op == "add_jobs":
                jobs = payload.get("jobs") or []
                if not jobs:
                    sheet_outbox.mark_dead(rid, "empty jobs payload", db_path=db_path)
                    continue
                os.environ["SHEET_TAB_DATE"] = tab
                client.connect()
                client.add_jobs(jobs)
            elif op == "update_eval":
                updates = payload.get("updates") or []
                if not updates:
                    sheet_outbox.mark_dead(rid, "empty updates payload", db_path=db_path)
                    continue
                os.environ["SHEET_TAB_DATE"] = tab
                client.connect()
                ws = client._open_workbook().worksheet(tab)
                client.update_evaluated_jobs(ws, updates)
            else:
                sheet_outbox.mark_dead(rid, f"unknown op {op}", db_path=db_path)
                continue
            sheet_outbox.mark_synced(rid, db_path=db_path)
            print(f"[outbox] id={rid} synced")
        except Exception as e:
            err = str(e)
            print(f"[outbox] id={rid} replay failed: {err}", file=sys.stderr)
            any_fail = True
            if args.mark_dead_on_error:
                sheet_outbox.mark_dead(rid, err, db_path=db_path)
            else:
                sheet_outbox.bump_attempt(rid, err, db_path=db_path)
    if any_fail:
        return 1

    if args.also_json_dir.strip():
        jdir = Path(args.also_json_dir.strip())
        if not jdir.is_dir():
            print(f"--also-json-dir not a directory: {jdir}", file=sys.stderr)
            return 1
        os.environ.pop("SHEET_TAB_DATE", None)
        jc = GoogleSheetsClient()
        jr = _replay_json_dir(jc, jdir, args.dry_run, args.json_move_on_success)
        if jr:
            return jr

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
