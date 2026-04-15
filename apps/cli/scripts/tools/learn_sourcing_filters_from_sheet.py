#!/usr/bin/env python3
"""
Mine title phrases from evaluated Google Sheet rows that were a poor fit vs good fit,
write data/sourcing_learned_title_blocks.yaml for early sourcing drops (saves eval tokens).

This is interpretable frequency/lift mining, not a neural model. Review and trim phrases
before setting sourcing.apply_learned_title_blocks: true in config/pipeline.yaml.

Usage (repo root):
  python3 apps/cli/scripts/tools/learn_sourcing_filters_from_sheet.py
  python3 apps/cli/scripts/tools/learn_sourcing_filters_from_sheet.py --dry-run
  python3 apps/cli/scripts/tools/learn_sourcing_filters_from_sheet.py --neg-max-score 50 --pos-min-score 72
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import yaml

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient
from apps.cli.legacy.core.sourcing_learned_blocks import mine_blocking_phrases


def _score_int(row: Dict[str, Any]) -> Optional[int]:
    raw = str(row.get("Apply Score", "")).strip()
    if not raw:
        return None
    try:
        return int(float(raw))
    except ValueError:
        return None


def classify_row(
    row: Dict[str, Any],
    *,
    neg_max_score: int,
    pos_min_score: int,
) -> Optional[str]:
    """Return 'neg', 'pos', or None (ambiguous / skip)."""
    st = str(row.get("Status", "")).strip().upper()
    if st != "EVALUATED":
        return None

    fb = str(row.get("Feedback", "")).strip().lower()
    if fb in ("thumbs_down", "down", "no", "n", "👎"):
        return "neg"
    if fb in ("thumbs_up", "up", "yes", "y", "👍"):
        return "pos"

    sc = _score_int(row)
    mt = str(row.get("Match Type", "")).lower()

    if sc is not None and sc <= neg_max_score:
        return "neg"
    if "❌" in str(row.get("Match Type", "")) or "low priority" in mt:
        if sc is None or sc < pos_min_score:
            return "neg"
    if sc is not None and sc >= pos_min_score:
        if "strong" in mt or "must" in mt or "worth considering" in mt or "ambitious" in mt:
            return "pos"
    if sc is not None and sc >= pos_min_score:
        return "pos"
    return None


def fetch_evaluated_rows(client: GoogleSheetsClient) -> List[Dict[str, Any]]:
    client.connect()
    wb = client._open_workbook()
    out: List[Dict[str, Any]] = []
    for ws in wb.worksheets():
        for r in ws.get_all_records():
            r["_sheet_tab"] = ws.title
            out.append(r)
    return out


def learn_from_sheet(
    *,
    out: str = "data/sourcing_learned_title_blocks.yaml",
    neg_max_score: int = 48,
    pos_min_score: int = 72,
    min_neg_count: int = 3,
    min_lift: float = 2.0,
    max_phrases: int = 80,
    dry_run: bool = False,
) -> str:
    """Mine and optionally persist learned blocking phrases; returns output path."""
    os.chdir(PROJECT_ROOT)
    client = GoogleSheetsClient()
    rows = fetch_evaluated_rows(client)

    neg_titles: List[str] = []
    pos_titles: List[str] = []
    skipped = 0
    for r in rows:
        lab = classify_row(
            r, neg_max_score=neg_max_score, pos_min_score=pos_min_score
        )
        title = str(r.get("Role Title", "") or "").strip()
        if not title:
            skipped += 1
            continue
        if lab == "neg":
            neg_titles.append(title)
        elif lab == "pos":
            pos_titles.append(title)
        else:
            skipped += 1

    mined = mine_blocking_phrases(
        neg_titles,
        pos_titles,
        min_neg_count=min_neg_count,
        min_lift=min_lift,
        max_phrases=max_phrases,
    )

    out_path = out if os.path.isabs(out) else os.path.join(PROJECT_ROOT, out)
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "params": {
            "neg_max_score": neg_max_score,
            "pos_min_score": pos_min_score,
            "min_neg_count": min_neg_count,
            "min_lift": min_lift,
        },
        "stats": {
            "sheet_rows_evaluated_labeled_negative": len(neg_titles),
            "sheet_rows_evaluated_labeled_positive": len(pos_titles),
            "rows_skipped_unlabeled": skipped,
        },
        "blocked_phrases": mined,
    }

    print(
        f"Labeled negatives: {len(neg_titles)} positives: {len(pos_titles)} "
        f"skipped/unlabeled: {skipped}"
    )
    print(f"Mined {len(mined)} blocking phrases (review before enabling apply_learned_title_blocks).")
    for p in mined[:25]:
        print(f"  - {p['text']!r}  (neg={p['negative_hits']} pos={p['positive_hits']} lift={p['lift']})")
    if len(mined) > 25:
        print(f"  ... and {len(mined) - 25} more")

    if dry_run:
        return out_path

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(payload, f, sort_keys=False, allow_unicode=True)
    print(f"Wrote {out_path}")
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser(description="Learn sourcing title blocks from sheet history")
    ap.add_argument("--dry-run", action="store_true", help="Print summary only; do not write YAML")
    ap.add_argument("--out", default="data/sourcing_learned_title_blocks.yaml", help="Output path")
    ap.add_argument("--neg-max-score", type=int, default=48, help="Rows at or below = negative label")
    ap.add_argument("--pos-min-score", type=int, default=72, help="Rows at or above = positive label")
    ap.add_argument("--min-neg-count", type=int, default=3, help="Min occurrences in negative titles")
    ap.add_argument("--min-lift", type=float, default=2.0, help="Min neg/pos rate lift")
    ap.add_argument("--max-phrases", type=int, default=80)
    args = ap.parse_args()
    learn_from_sheet(
        out=args.out,
        neg_max_score=args.neg_max_score,
        pos_min_score=args.pos_min_score,
        min_neg_count=args.min_neg_count,
        min_lift=args.min_lift,
        max_phrases=args.max_phrases,
        dry_run=args.dry_run,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
