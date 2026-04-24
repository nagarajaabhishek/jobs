#!/usr/bin/env python3
"""
Backfill Manual_JD_Tailor validation columns for rows that already have tailored YAML
but were processed before variant scoring was written to the sheet.

Usage (repo root):
  python3 scripts/tools/backfill_manual_tailor_validation.py --from-tailor-tab
  python3 scripts/tools/backfill_manual_tailor_validation.py "https://jobright.ai/jobs/info/..."
"""
from __future__ import annotations

import argparse
import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.agents.evaluate_jobs import JobEvaluator  # noqa: E402
from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient  # noqa: E402
from core_agents.resume_agent.tailor import TailorAgent  # noqa: E402
from scripts.tools.tailor_from_urls import compare_tailored_vs_generic_for_job  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Backfill tailored vs generic validation scores on Manual_JD_Tailor.")
    ap.add_argument("urls", nargs="*", help="Optional explicit URLs (otherwise use --from-tailor-tab)")
    ap.add_argument(
        "--from-tailor-tab",
        action="store_true",
        help="Use all jobs from Manual_JD_Tailor (Job Link + Recommended Resume).",
    )
    ap.add_argument("--profile", default="", help="Override resume.profile")
    ap.add_argument("--base-yaml", default="", help="Override resume.base_role_yaml")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
    except ImportError:
        pass

    client = GoogleSheetsClient()
    client.connect()

    if args.from_tailor_tab:
        jobs = client.read_manual_jd_tailor_jobs()
    else:
        jobs = [{"url": u.strip(), "recommended_resume": ""} for u in args.urls if u.strip()]

    if not jobs:
        print("No URLs to process.", file=sys.stderr)
        return 2

    tailor = TailorAgent(
        profile=args.profile.strip() or None,
        base_role_yaml=args.base_yaml.strip() or None,
    )
    evaluator = JobEvaluator()

    for job in jobs:
        url = job["url"]
        rec = (job.get("recommended_resume") or "").strip()
        jd_text = (client.get_jd_for_url(url) or "").strip()
        if not jd_text:
            msg = "JD not in cache; run tailor_from_urls or ingest first."
            if args.json:
                print(json.dumps({"url": url, "error": msg}, ensure_ascii=False))
            else:
                print(f"{url}\n  SKIP: {msg}")
            continue

        vv, vr, ts, gs, use_resume = compare_tailored_vs_generic_for_job(
            tailor, url, jd_text, rec, evaluator=evaluator
        )

        ok = client.update_manual_jd_tailor_validation_only(
            url=url,
            validation_verdict=vv,
            validation_reason=vr,
            tailored_score=ts,
            generic_score=gs,
            use_resume=use_resume,
        )

        line = {
            "url": url,
            "recommended_resume": rec,
            "validation_verdict": vv,
            "validation_reason": vr,
            "tailored_score": ts,
            "generic_score": gs,
            "use_resume": use_resume,
            "sheet_updated": ok,
        }
        if args.json:
            print(json.dumps(line, ensure_ascii=False))
        else:
            print(f"\n{url}")
            print(f"  Verdict: {vv or '(none)'}  tailored={ts}  generic={gs}  -> {use_resume}")
            print(f"  Sheet updated: {ok}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
