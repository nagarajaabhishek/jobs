#!/usr/bin/env python3
"""
Sourcing advisor: rank job *sources* and *companies* from your own sheet history
(no LLM). Use this to decide where to spend crawl/eval tokens for a given role focus.

Reads dated tabs (YYYY-MM-DD), rows with Status=EVALUATED and Apply Score set.
Outputs human-readable summary and optional YAML under data/.

Usage (repo root):
  python3 apps/cli/scripts/tools/suggest_sourcing_sources.py
  python3 apps/cli/scripts/tools/suggest_sourcing_sources.py --recent-tabs 14 --min-rows-per-source 3
  python3 apps/cli/scripts/tools/suggest_sourcing_sources.py --output data/sourcing_hints.yaml
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import yaml

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient


def _score_float(row: Dict[str, Any]) -> Optional[float]:
    raw = str(row.get("Apply Score", "")).strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _role_family(title: str) -> str:
    t = (title or "").lower()
    if "business analyst" in t or re.search(r"\bba\b", t):
        return "business_analyst"
    if "product owner" in t or re.search(r"\bpo\b", t) or "product owner" in t:
        return "product_owner"
    if "product manager" in t or re.search(r"\bpm\b", t):
        return "product_manager"
    if "project manager" in t or "program manager" in t:
        return "project_program"
    if "scrum" in t or "agile coach" in t:
        return "agile"
    return "other"


@dataclass
class Bucket:
    n: int = 0
    sum_score: float = 0.0
    ge_70: int = 0
    ge_80: int = 0


def _add(b: Bucket, score: float, thr_70: float, thr_80: float) -> None:
    b.n += 1
    b.sum_score += score
    if score >= thr_70:
        b.ge_70 += 1
    if score >= thr_80:
        b.ge_80 += 1


def _bucket_summary(b: Bucket) -> Dict[str, Any]:
    if b.n == 0:
        return {"n": 0, "mean_score": 0.0, "rate_ge_70": 0.0, "rate_ge_80": 0.0}
    return {
        "n": b.n,
        "mean_score": round(b.sum_score / b.n, 2),
        "rate_ge_70": round(100 * b.ge_70 / b.n, 1),
        "rate_ge_80": round(100 * b.ge_80 / b.n, 1),
        "count_ge_70": b.ge_70,
        "count_ge_80": b.ge_80,
    }


def _quality_score(b: Bucket, min_n: int) -> float:
    """Heuristic ranking: volume + hit rate for high scores."""
    if b.n < min_n:
        return -1.0
    rate80 = b.ge_80 / b.n
    rate70 = b.ge_70 / b.n
    return b.n * (2.0 * rate80 + rate70)


def collect_rows(
    client: GoogleSheetsClient,
    *,
    recent_tabs: int,
    tab_glob: Optional[str],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    client.connect()
    wb = client._open_workbook()
    tab_titles: List[str] = []
    for ws in wb.worksheets():
        t = (ws.title or "").strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
            tab_titles.append(t)
    tab_titles.sort(reverse=True)
    if tab_glob:
        tab_titles = [t for t in tab_titles if tab_glob in t][:recent_tabs]
    else:
        tab_titles = tab_titles[:recent_tabs]

    rows_out: List[Dict[str, Any]] = []
    for title in tab_titles:
        try:
            ws = wb.worksheet(title)
        except Exception:
            continue
        for r in ws.get_all_records():
            r = dict(r)
            r["_tab"] = title
            rows_out.append(r)
    return rows_out, tab_titles


def build_report(
    rows: List[Dict[str, Any]],
    *,
    thr_70: float,
    thr_80: float,
    min_rows_source: int,
    top_sources: int,
    top_companies: int,
) -> Dict[str, Any]:
    by_source: Dict[str, Bucket] = defaultdict(Bucket)
    by_company: Dict[str, Bucket] = defaultdict(Bucket)
    by_source_role: Dict[Tuple[str, str], Bucket] = defaultdict(Bucket)

    used = 0
    for r in rows:
        st = str(r.get("Status", "")).strip().upper()
        if st != "EVALUATED":
            continue
        sc = _score_float(r)
        if sc is None:
            continue
        src = str(r.get("Source", "") or "").strip() or "unknown"
        co = str(r.get("Company", "") or "").strip() or "unknown"
        title = str(r.get("Role Title", "") or "")
        fam = _role_family(title)
        _add(by_source[src], sc, thr_70, thr_80)
        _add(by_source_role[(src, fam)], sc, thr_70, thr_80)
        if sc >= thr_70:
            _add(by_company[co], sc, thr_70, thr_80)
        used += 1

    sources_ranked = sorted(
        by_source.keys(),
        key=lambda s: _quality_score(by_source[s], min_rows_source),
        reverse=True,
    )
    companies_ranked = sorted(
        by_company.keys(),
        key=lambda c: _quality_score(by_company[c], min_rows_source),
        reverse=True,
    )

    payload: Dict[str, Any] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "params": {
            "threshold_ge_70": thr_70,
            "threshold_ge_80": thr_80,
            "min_rows_per_source": min_rows_source,
            "evaluated_rows_used": used,
        },
        "top_sources": [],
        "top_companies_for_high_scores": [],
        "sources_by_role_family": defaultdict(dict),
    }

    for s in sources_ranked:
        if _quality_score(by_source[s], min_rows_source) < 0:
            continue
        payload["top_sources"].append(
            {
                "source": s,
                **_bucket_summary(by_source[s]),
                "rank_score": round(_quality_score(by_source[s], min_rows_source), 2),
            }
        )
        if len(payload["top_sources"]) >= top_sources:
            break

    for c in companies_ranked:
        if _quality_score(by_company[c], min_rows_source) < 0:
            continue
        payload["top_companies_for_high_scores"].append(
            {
                "company": c,
                **_bucket_summary(by_company[c]),
                "rank_score": round(_quality_score(by_company[c], min_rows_source), 2),
            }
        )
        if len(payload["top_companies_for_high_scores"]) >= top_companies:
            break

    families = {"product_manager", "business_analyst", "product_owner", "project_program", "agile"}
    for (src, fam), b in by_source_role.items():
        if fam not in families or b.n < min_rows_source:
            continue
        payload["sources_by_role_family"][fam][src] = _bucket_summary(b)

    # Convert defaultdict to plain dict for YAML
    payload["sources_by_role_family"] = {
        k: dict(v) for k, v in sorted(payload["sources_by_role_family"].items())
    }
    return payload


def run_sourcing_hints(
    *,
    project_root: Optional[str] = None,
    recent_tabs: int = 21,
    tab_filter: str = "",
    thr_70: float = 70.0,
    thr_80: float = 80.0,
    min_rows_per_source: int = 5,
    top_sources: int = 25,
    top_companies: int = 40,
    output_path: str = "data/sourcing_hints.yaml",
    quiet: bool = False,
    client: Optional[GoogleSheetsClient] = None,
) -> Dict[str, Any]:
    """
    Scan dated sheet tabs and write ranked sourcing hints (sources / companies / role families).
    Used by the CLI and by run_pipeline cycle hooks.
    """
    root = project_root or PROJECT_ROOT
    prev_cwd = os.getcwd()
    try:
        os.chdir(root)
        gc = client or GoogleSheetsClient()
        rows, tabs = collect_rows(
            gc,
            recent_tabs=max(1, recent_tabs),
            tab_glob=tab_filter.strip() or None,
        )
        if not quiet:
            suffix = "…" if len(tabs) > 5 else ""
            print(f"Scanned tabs ({len(tabs)}): {', '.join(tabs[:5])}{suffix}")

        report = build_report(
            rows,
            thr_70=thr_70,
            thr_80=thr_80,
            min_rows_source=max(1, min_rows_per_source),
            top_sources=max(1, top_sources),
            top_companies=max(1, top_companies),
        )
        if not quiet:
            print_summary(report)

        out = (output_path or "").strip()
        if out:
            path = out if os.path.isabs(out) else os.path.join(root, out)
            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(report, f, sort_keys=False, allow_unicode=True)
            if not quiet:
                print(f"\nWrote {path}")
        return report
    finally:
        os.chdir(prev_cwd)


def print_summary(report: Dict[str, Any]) -> None:
    print("\n--- Sourcing hints (from your sheet history) ---")
    print(f"Evaluated rows used: {report['params']['evaluated_rows_used']}")
    print("\nTop sources (volume + high-score rate):")
    for row in report.get("top_sources", [])[:15]:
        print(
            f"  - {row['source']!r}: n={row['n']} mean={row['mean_score']} "
            f">={report['params']['threshold_ge_70']:.0f}%: {row['rate_ge_70']}%  "
            f">={report['params']['threshold_ge_80']:.0f}%: {row['rate_ge_80']}%"
        )
    print("\nCompanies (among rows already >= 70; shows who hires strong matches more often):")
    for row in report.get("top_companies_for_high_scores", [])[:12]:
        print(
            f"  - {row['company']!r}: n={row['n']} mean={row['mean_score']} "
            f">=80 rate: {row['rate_ge_80']}%"
        )
    print("\nPer role family — best sources (min volume):")
    for fam, mp in report.get("sources_by_role_family", {}).items():
        ranked = sorted(mp.items(), key=lambda x: x[1].get("count_ge_80", 0), reverse=True)[:5]
        print(f"  [{fam}]")
        for src, stats in ranked:
            print(f"     {src!r}: n={stats['n']} >=80: {stats['count_ge_80']}  mean={stats['mean_score']}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Suggest sourcing focus from sheet history")
    ap.add_argument("--recent-tabs", type=int, default=21, help="How many recent dated tabs to scan")
    ap.add_argument("--tab-filter", type=str, default="", help="Substring filter on tab title (optional)")
    ap.add_argument("--thr-70", type=float, default=70.0)
    ap.add_argument("--thr-80", type=float, default=80.0)
    ap.add_argument("--min-rows-per-source", type=int, default=5)
    ap.add_argument("--top-sources", type=int, default=25)
    ap.add_argument("--top-companies", type=int, default=40)
    ap.add_argument("--output", type=str, default="", help="Write YAML (e.g. data/sourcing_hints.yaml)")
    ap.add_argument("--quiet", action="store_true", help="Only write file, minimal stdout")
    args = ap.parse_args()
    run_sourcing_hints(
        project_root=PROJECT_ROOT,
        recent_tabs=args.recent_tabs,
        tab_filter=args.tab_filter,
        thr_70=args.thr_70,
        thr_80=args.thr_80,
        min_rows_per_source=args.min_rows_per_source,
        top_sources=args.top_sources,
        top_companies=args.top_companies,
        output_path=args.output.strip(),
        quiet=args.quiet,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
