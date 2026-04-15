#!/usr/bin/env python3
"""
Evaluate one or more job URLs with the legacy JobEvaluator (same prompt/parser as the pipeline).

If a URL is not in config/jd_cache.json, runs the sourcing agent's static/Playwright JD fetch,
writes the result to the cache, then evaluates.

Usage (from repo root):
  python3 apps/cli/scripts/tools/eval_test_urls.py "https://..." "https://..."
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# tools -> scripts -> cli -> apps -> repo root (4 levels up)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.agents.evaluate_jobs import JobEvaluator  # noqa: E402
from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient  # noqa: E402
from apps.cli.legacy.core.jd_cache_helpers import ensure_jd_cached  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Test legacy job evaluator on arbitrary URLs.")
    ap.add_argument("urls", nargs="+", help="One or more job posting URLs")
    ap.add_argument("--json", action="store_true", help="Print machine-readable JSON lines")
    args = ap.parse_args()

    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
    except ImportError:
        pass

    client = GoogleSheetsClient()
    client.connect()
    evaluator = JobEvaluator()

    for url in args.urls:
        url = url.strip()
        ok, jd_msg = ensure_jd_cached(client, url, project_root=PROJECT_ROOT)
        if not ok:
            line = {"url": url, "error": jd_msg}
            print(json.dumps(line, ensure_ascii=False) if args.json else f"\n{url}\n  SKIP: {jd_msg}")
            continue
        try:
            out = evaluator.evaluate_single_job(url)
        except Exception as e:
            line = {"url": url, "jd": jd_msg, "error": str(e)}
            print(json.dumps(line, ensure_ascii=False) if args.json else f"\n{url}\n  EVAL ERROR: {e}")
            continue
        if args.json:
            out = dict(out)
            out["url"] = url
            out["jd_source"] = jd_msg
            print(json.dumps(out, ensure_ascii=False))
        else:
            print(f"\n{'=' * 72}\n{url}\nJD: {jd_msg}")
            print(f"Verdict: {out.get('verdict')}  |  Score: {out.get('score')}")
            if out.get("base_llm_score") is not None:
                print(f"Base LLM score: {out.get('base_llm_score')}  Δ cal: {out.get('calibration_delta', 0)}")
            print(f"Recommended resume: {out.get('recommended_resume')}")
            print(f"H1B: {out.get('h1b')}")
            print(f"Missing / gaps: {out.get('missing_skills')}")
            print(f"Salary: {out.get('salary')}")
            print(f"Tech: {out.get('tech_stack')}")
            print(f"Reasoning:\n{out.get('reasoning', '')[:4000]}")
            if len(str(out.get("reasoning", ""))) > 4000:
                print("… (truncated in console)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
