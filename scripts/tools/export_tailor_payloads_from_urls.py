#!/usr/bin/env python3
"""
Emit data/tailor_payloads/*.json from plain job URLs (no evaluated sheet rows, no re-LLM eval).
Fetches JD into jd_cache if missing, then writes JSON for external PDF/LaTeX tools.

Usage (repo root):
  python3 scripts/tools/export_tailor_payloads_from_urls.py "https://..." "https://..."
  python3 scripts/tools/export_tailor_payloads_from_urls.py --file urls.txt
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient, normalize_job_url  # noqa: E402
from apps.cli.legacy.core.jd_cache_helpers import ensure_jd_cached  # noqa: E402


def _read_urls(path: str | None, extra: list[str]) -> list[str]:
    raw: list[str] = []
    if path:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    raw.append(line)
    raw.extend(extra)
    seen: set[str] = set()
    out: list[str] = []
    for u in raw:
        u = u.strip()
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Export tailor JSON payloads from job URLs + jd_cache.")
    p.add_argument("urls", nargs="*", help="Job posting URLs")
    p.add_argument("-f", "--file", help="One URL per line")
    args = p.parse_args()

    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
    except ImportError:
        pass

    urls = _read_urls(args.file, list(args.urls))
    if not urls:
        print("No URLs.", file=sys.stderr)
        return 2

    client = GoogleSheetsClient()
    client.connect()

    out_dir = os.path.join(PROJECT_ROOT, "data", "tailor_payloads")
    os.makedirs(out_dir, exist_ok=True)

    written = 0
    for url in urls:
        ok, jd_msg = ensure_jd_cached(client, url, project_root=PROJECT_ROOT)
        jd = (client.get_jd_for_url(url) or "").strip()
        if not ok or not jd:
            print(f"skip {url!r}: {jd_msg}", file=sys.stderr)
            continue

        canon = normalize_job_url(url) or url
        stem = hashlib.sha256(canon.encode("utf-8")).hexdigest()[:12]

        payload = {
            "exported_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "source": "export_tailor_payloads_from_urls.py",
            "job_link": url,
            "canonical_url": canon,
            "jd_fetch_note": jd_msg,
            "apply_conviction_score": None,
            "apply_bucket": "",
            "recommended_resume": "",
            "skill_gaps": [],
            "jd_excerpt": jd[:12000],
            "reasoning_excerpt": "",
            "notes": "URL-only export; no pipeline eval. Verify JD and tailor externally.",
        }

        fname = f"url_{stem}.json"
        path = os.path.join(out_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(path)
        written += 1

    print(f"Wrote {written} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
