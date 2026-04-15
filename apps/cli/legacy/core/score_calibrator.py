"""Post-LLM score calibration from learned patterns (bounded 0-100)."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import yaml

from apps.cli.legacy.core.learning_schemas import DecisionAudit, LearnedPattern

DEFAULT_PATTERNS_PATH = os.path.join(os.getcwd(), "data", "learned_patterns.yaml")


def _coerce_sheet_text(val: Any) -> str:
    """Sheets / pandas often surface empty cells as float NaN; str() alone breaks str.join."""
    if val is None:
        return ""
    if isinstance(val, float) and val != val:  # NaN
        return ""
    try:
        s = str(val).strip()
    except Exception:
        return ""
    if s.lower() in ("nan", "none", "nat"):
        return ""
    return s


def _load_patterns(path: str | None = None) -> List[LearnedPattern]:
    p = path or DEFAULT_PATTERNS_PATH
    if not os.path.isfile(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        items = raw.get("patterns", []) if isinstance(raw, dict) else raw
        if not isinstance(items, list):
            return []
        out: List[LearnedPattern] = []
        for it in items:
            if isinstance(it, dict):
                out.append(LearnedPattern.from_dict(it))
        return out
    except Exception:
        return []


def compute_calibration_delta(
    jd_text: str,
    title: str = "",
    company: str = "",
    patterns: List[LearnedPattern] | None = None,
    max_abs_delta: int = 15,
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Sum pattern contributions: boost adds, penalize subtracts.
    Each pattern matches if pattern_value (lowercased) appears in haystack.
    Delta is clamped to [-max_abs_delta, max_abs_delta].
    """
    hay = " ".join(
        [
            _coerce_sheet_text(jd_text),
            _coerce_sheet_text(title),
            _coerce_sheet_text(company),
        ]
    ).lower()
    if not hay.strip():
        return 0, []

    plist = patterns if patterns is not None else _load_patterns()
    delta = 0.0
    matched: List[Dict[str, Any]] = []

    for pat in plist:
        pv = (pat.pattern_value or "").strip().lower()
        if len(pv) < 2:
            continue
        if pv not in hay:
            continue
        w = pat.weight_adjustment * max(0.1, min(1.0, pat.confidence))
        if pat.pattern_type == "penalize":
            delta -= w
        else:
            delta += w
        matched.append(
            {
                "pattern_type": pat.pattern_type,
                "pattern_value": pat.pattern_value,
                "contribution": round(w, 4) if pat.pattern_type == "boost" else -round(w, 4),
            }
        )

    int_delta = int(round(delta))
    int_delta = max(-max_abs_delta, min(max_abs_delta, int_delta))
    return int_delta, matched


def apply_calibration(
    base_score: int,
    jd_text: str,
    title: str = "",
    company: str = "",
    patterns: List[LearnedPattern] | None = None,
    max_abs_delta: int = 15,
    cycle_id: str = "",
) -> Tuple[int, DecisionAudit]:
    """Return final clamped score and audit object."""
    base = max(0, min(100, int(base_score)))
    cal_delta, matched = compute_calibration_delta(
        jd_text, title=title, company=company, patterns=patterns, max_abs_delta=max_abs_delta
    )
    final = max(0, min(100, base + cal_delta))
    audit = DecisionAudit(
        base_llm_score=base,
        calibration_delta=cal_delta,
        final_score=final,
        matched_patterns=matched,
        cycle_id=cycle_id or "",
        notes="",
    )
    return final, audit
