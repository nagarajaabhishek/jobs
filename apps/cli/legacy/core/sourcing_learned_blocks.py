"""
Learn title phrases from labeled job rows (sheet history) to block noisy sourcing early.

This is interpretable pattern mining, not a neural model. Human review recommended before
enabling sourcing.apply_learned_title_blocks in config/pipeline.yaml.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Tuple

import yaml

# Generic role words that rarely discriminate bad vs good fits (skip as mined blocks)
_STOP_FEATURES = frozenset(
    {
        "manager",
        "product",
        "project",
        "program",
        "business",
        "analyst",
        "owner",
        "scrum",
        "master",
        "remote",
        "hybrid",
        "full",
        "time",
        "with",
        "this",
        "that",
        "from",
        "your",
        "our",
        "the",
        "and",
        "for",
    }
)


def title_features(title: str) -> List[str]:
    """Unigrams (len>=4) and adjacent bigrams, lowercased, de-noised."""
    t = re.sub(r"[^\w\s]", " ", (title or "").lower())
    words = [w for w in t.split() if len(w) >= 4 and w not in _STOP_FEATURES]
    out: List[str] = []
    seen = set()
    for w in words:
        if w not in seen:
            seen.add(w)
            out.append(w)
    for i in range(len(words) - 1):
        bg = f"{words[i]} {words[i + 1]}"
        if bg not in seen:
            seen.add(bg)
            out.append(bg)
    return out


def mine_blocking_phrases(
    negative_titles: List[str],
    positive_titles: List[str],
    *,
    min_neg_count: int = 3,
    min_lift: float = 2.0,
    max_phrases: int = 80,
) -> List[Dict[str, Any]]:
    """
    Return phrase dicts over-represented in negative titles vs positive (lift = neg_rate / pos_rate).
    """
    neg_c: Dict[str, int] = {}
    pos_c: Dict[str, int] = {}
    for ti in negative_titles:
        for f in title_features(ti):
            neg_c[f] = neg_c.get(f, 0) + 1
    for ti in positive_titles:
        for f in title_features(ti):
            pos_c[f] = pos_c.get(f, 0) + 1

    n_n = max(1, len(negative_titles))
    n_p = max(1, len(positive_titles))
    scored: List[Tuple[float, str, int, int]] = []
    for phrase, c_neg in neg_c.items():
        if c_neg < min_neg_count:
            continue
        c_pos = pos_c.get(phrase, 0)
        rate_n = c_neg / n_n
        rate_p = (c_pos + 0.5) / n_p
        lift = rate_n / max(rate_p, 1e-6)
        if lift < min_lift:
            continue
        if c_pos > c_neg:
            continue
        scored.append((lift, phrase, c_neg, c_pos))

    scored.sort(key=lambda x: (-x[0], -x[2], x[1]))
    out: List[Dict[str, Any]] = []
    for lift, phrase, c_neg, c_pos in scored[:max_phrases]:
        out.append(
            {
                "text": phrase,
                "negative_hits": c_neg,
                "positive_hits": c_pos,
                "lift": round(lift, 3),
            }
        )
    return out


_CACHE: tuple[float, tuple[str, ...]] | None = None


def load_learned_blocked_phrases_for_filter(
    *,
    project_root: str | None = None,
    sourcing_cfg: Dict[str, Any] | None = None,
) -> List[str]:
    """Return lowercase phrases to match against job titles when apply flag is on."""
    global _CACHE
    if sourcing_cfg is None:
        from apps.cli.legacy.core.config import get_sourcing_config

        sourcing_cfg = get_sourcing_config()
    if not sourcing_cfg.get("apply_learned_title_blocks"):
        return []

    root = (project_root or "").strip() or os.getcwd()
    rel = sourcing_cfg.get("learned_title_blocks_path", "data/sourcing_learned_title_blocks.yaml")
    path = rel if os.path.isabs(rel) else os.path.join(root, rel)
    if not os.path.isfile(path):
        return []
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return []
    if _CACHE is not None and _CACHE[0] == mtime:
        return list(_CACHE[1])

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except OSError:
        return []

    raw = data.get("blocked_phrases") or []
    out: List[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            out.append(item.strip().lower())
        elif isinstance(item, dict):
            t = str(item.get("text") or item.get("phrase") or "").strip()
            if t:
                out.append(t.lower())
    # de-dup preserve order
    seen = set()
    deduped = []
    for p in out:
        if p not in seen:
            seen.add(p)
            deduped.append(p)
    _CACHE = (mtime, tuple(deduped))
    return deduped


def learned_block_hit(title: str, phrases: List[str]) -> str | None:
    """Return matched phrase or None. Multi-word = substring; single word = word boundary."""
    title_lower = str(title or "").lower()
    if not title_lower.strip():
        return None
    for p in phrases:
        pl = (p or "").strip().lower()
        if not pl:
            continue
        if " " in pl:
            if pl in title_lower:
                return pl
        else:
            if re.search(r"\b" + re.escape(pl) + r"\b", title_lower):
                return pl
    return None
