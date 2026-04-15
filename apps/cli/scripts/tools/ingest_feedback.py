#!/usr/bin/env python3
"""
Ingest user feedback from Google Sheets (Feedback / Feedback Note columns) or a JSONL file,
append events to data/feedback_events.jsonl, and merge into data/learned_patterns.yaml.

Run from project root:
  python3 apps/cli/scripts/tools/ingest_feedback.py
  python3 apps/cli/scripts/tools/ingest_feedback.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import yaml  # type: ignore

from apps.cli.legacy.core.config import get_learning_config
from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient, normalize_job_url
from apps.cli.legacy.core.learning_schemas import (
    SHEET_COL_FEEDBACK,
    SHEET_COL_FEEDBACK_NOTE,
    FeedbackEvent,
    LearnedPattern,
)

EVENTS_PATH = os.path.join(PROJECT_ROOT, "data", "feedback_events.jsonl")
PATTERNS_PATH_DEFAULT = os.path.join(PROJECT_ROOT, "data", "learned_patterns.yaml")


def _tokenize_phrases(text: str, max_tokens: int = 12) -> List[str]:
    if not text:
        return []
    t = re.sub(r"[^\w\s\-]", " ", text.lower())
    parts = [p.strip() for p in re.split(r"[\s,;/]+", t) if len(p.strip()) >= 3]
    # de-dup preserve order
    seen = set()
    out: List[str] = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            out.append(p)
        if len(out) >= max_tokens:
            break
    return out


def _load_patterns(path: str) -> Tuple[Dict[Tuple[str, str], LearnedPattern], List[LearnedPattern]]:
    if not os.path.isfile(path):
        return {}, []
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        items = raw.get("patterns", []) if isinstance(raw, dict) else []
        lst: List[LearnedPattern] = []
        keymap: Dict[Tuple[str, str], LearnedPattern] = {}
        for it in items:
            if isinstance(it, dict):
                p = LearnedPattern.from_dict(it)
                keymap[(p.pattern_type, p.pattern_value.lower())] = p
                lst.append(p)
        return keymap, lst
    except Exception:
        return {}, []


def _save_patterns(path: str, patterns: List[LearnedPattern]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    data = {"patterns": [p.to_dict() for p in patterns]}
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=True, allow_unicode=True)


def _merge_pattern(
    keymap: Dict[Tuple[str, str], LearnedPattern],
    pattern_type: str,
    phrase: str,
    delta_weight: float,
) -> None:
    phrase = phrase.strip().lower()
    if len(phrase) < 3:
        return
    key = (pattern_type, phrase)
    if key in keymap:
        p = keymap[key]
        p.learned_from_count += 1
        p.weight_adjustment = min(10.0, p.weight_adjustment + delta_weight)
        p.confidence = min(1.0, p.confidence + 0.05)
    else:
        p = LearnedPattern(
            pattern_type=pattern_type,
            pattern_value=phrase,
            weight_adjustment=delta_weight,
            confidence=0.5,
            learned_from_count=1,
        )
        keymap[key] = p


def ingest_sheet_rows(dry_run: bool) -> int:
    client = GoogleSheetsClient()
    client.connect()
    today = datetime.now().strftime("%Y-%m-%d")
    ws = client.client.open(client.sheet_name).worksheet(today)
    values = ws.get_all_values()
    if not values or len(values) < 2:
        print("No rows to ingest.")
        return 0

    headers = [str(h).strip() for h in values[0]]
    def col_idx(name: str) -> int:
        try:
            return headers.index(name)
        except ValueError:
            return -1

    i_fb = col_idx(SHEET_COL_FEEDBACK)
    i_note = col_idx(SHEET_COL_FEEDBACK_NOTE)
    i_link = col_idx("Job Link")
    i_title = col_idx("Role Title")
    if i_fb == -1 or i_link == -1:
        print("Sheet missing Feedback or Job Link column; nothing to ingest.")
        return 0

    learn_cfg = get_learning_config()
    out_patterns = learn_cfg.get("patterns_path", "data/learned_patterns.yaml")
    ppath = out_patterns if os.path.isabs(out_patterns) else os.path.join(PROJECT_ROOT, out_patterns)

    keymap, _ = _load_patterns(ppath)
    processed = 0
    events: List[str] = []

    for row in values[1:]:
        while len(row) < len(headers):
            row.append("")
        fb = str(row[i_fb]).strip().lower() if i_fb >= 0 else ""
        if not fb or fb in ("", "pending"):
            continue
        note = str(row[i_note]).strip() if i_note >= 0 else ""
        link = row[i_link]
        title = str(row[i_title]).strip() if i_title >= 0 else ""
        canon = normalize_job_url(link)

        ev = FeedbackEvent(
            job_url_canonical=canon,
            feedback_type=fb,
            feedback_text=note,
            created_at=datetime.now().isoformat(timespec="seconds"),
            row_hint=title,
        )
        events.append(ev.to_json_line())

        # Derive patterns
        if fb in ("thumbs_up", "up", "yes", "y", "👍"):
            src = note if note else title
            for ph in _tokenize_phrases(src):
                _merge_pattern(keymap, "boost", ph, 1.5)
        elif fb in ("thumbs_down", "down", "no", "n", "👎"):
            src = note if note else title
            for ph in _tokenize_phrases(src):
                _merge_pattern(keymap, "penalize", ph, 1.5)
        elif fb == "note" or note:
            for ph in _tokenize_phrases(note):
                _merge_pattern(keymap, "boost", ph, 0.8)

        processed += 1

    merged_list = list(keymap.values())

    if not dry_run:
        os.makedirs(os.path.dirname(EVENTS_PATH) or ".", exist_ok=True)
        with open(EVENTS_PATH, "a", encoding="utf-8") as f:
            for line in events:
                f.write(line + "\n")
        _save_patterns(ppath, merged_list)
    else:
        print(f"[dry-run] Would append {len(events)} events and save {len(merged_list)} patterns.")

    print(f"Ingested feedback rows: {processed}")
    return processed


def main():
    ap = argparse.ArgumentParser(description="Ingest job feedback into learned_patterns.yaml")
    ap.add_argument("--dry-run", action="store_true", help="Do not write files")
    args = ap.parse_args()
    os.chdir(PROJECT_ROOT)
    ingest_sheet_rows(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
