"""
Shared job filter constants and logic for sourcing and evaluation.
Single source of truth so both pipelines stay in sync.
"""
from __future__ import annotations

import re
import logging
from collections import Counter
from typing import Any

from apps.cli.legacy.core.config import get_filters_config, get_sourcing_config, get_title_fit_config
from apps.cli.legacy.core.sourcing_learned_blocks import (
    learned_block_hit,
    load_learned_blocked_phrases_for_filter,
)
from apps.cli.legacy.core.title_fit_gate import evaluate_title_fit

# Defaults used when config/pipeline.yaml omits keys (also for tests)
_DEFAULT_INCLUSIONS = [
    "product manager", "project manager", "program manager",
    "business analyst", "product owner", "scrum master",
    "agile coach", "gtm", "go-to market", "strategy", "operations analyst",
    "product lead", "project lead", "program lead", "delivery manager",
    "operations manager", "business operations", "chief of staff",
    "ba", "pm", "po", "tpm", "pmo", "scrum", "agile",
]

_DEFAULT_SENIOR_EXCLUSIONS = [
    "senior", "sr", "sr.", "staff", "principal", "director",
    "vp", "head of", "lead", "manager ii",
]

_DEFAULT_SOFT_BYPASS = [
    "product manager", "product owner", "project manager", "program manager",
    "business analyst", "scrum master", "product lead", "project lead",
    "program lead", "technical program", "agile coach", "product director",
    "program director", "director of product", "project director",
]

# Load dynamic filters (legacy module-level; prefer get_filters_config() in passes_*)
_f = get_filters_config()
TITLE_INCLUSIONS = _f.get("inclusions", _DEFAULT_INCLUSIONS)
SENIOR_KEYWORDS = _f.get("seniority_exclusions", _DEFAULT_SENIOR_EXCLUSIONS)
LEVEL_EXCLUSIONS = _f.get("level_exclusions", [
    "intern", "internship", "co-op", "graduate intern", "student intern",
])
CLEARANCE_KEYWORDS = _f.get("clearance_keywords", [
    "clearance", "ts/sci", "secret clearance", "top secret",
])
UNRELATED_KEYWORDS = _f.get("unrelated_keywords", [
    "nurse", "registered nurse", "rn", "physician", "driver", "cdl",
    "warehouse", "mechanic", "cashier", "architect", "software engineer",
    "backend", "frontend", "fullstack", "full stack", "account executive", "recruiter",
    "firmware", "hardware", "validation", "characterization",
    "testing engineer", "product engineer", "data analyst",
])
UNRELATED_TEXT_KEYWORDS = _f.get("unrelated_text_keywords", [])

ALLOWED_LOCATIONS = _f.get("allowed_locations", [
    "usa", "united states", "dubai", "uae", "remote", "us",
    ", al", ", ak", ", az", ", ar", ", ca", ", co", ", ct", ", de", ", fl", ", ga",
    ", hi", ", id", ", il", ", in", ", ia", ", ks", ", ky", ", la", ", me", ", md",
    ", ma", ", mi", ", mn", ", ms", ", mo", ", mt", ", ne", ", nv", ", nh", ", nj",
    ", nm", ", ny", ", nc", ", nd", ", oh", ", ok", ", or", ", pa", ", ri", ", sc",
    ", sd", ", tn", ", tx", ", ut", ", vt", ", va", ", wa", ", wv", ", wi", ", wy",
    ", dc",
])
LOCATION_EXCLUSIONS = _f.get("forbidden_locations", [
    "india", "uk", "london", "canada", "australia", "germany", "france",
    "singapore", "bangalore", "hyderabad", "toronto",
    "munich", "berlin", "dresden", "frankfurt", "europe",
])

# Non-US markers in title (sourcing)
TITLE_NON_US_MARKERS = ["(m/w/d)", "(all genders)"]

def normalize_sourcing_location(location: str, title: str = "") -> str:
    """Normalize location string for substring checks (common JobSpy variants)."""
    loc = " ".join(str(location or "").lower().split())
    if not loc and title:
        t = str(title).lower()
        if "remote" in t or "work from home" in t or "wfh" in t:
            loc = "remote"
    replacements = (
        ("united states of america", "united states"),
        ("u.s.a.", "usa"),
        ("u.s.", "usa"),
    )
    for a, b in replacements:
        loc = loc.replace(a, b)
    return loc.strip()


def _forbidden_location_hits(location_norm: str, title_lower: str, forbidden_list: list[str]) -> str | None:
    """Return forbidden token that matched, or None. Single-token entries use word boundaries (avoids India vs Indiana)."""
    for exc in forbidden_list:
        e = exc.strip().lower()
        if not e:
            continue
        if " " in e:
            pattern = re.escape(e)
        else:
            pattern = r"\b" + re.escape(e) + r"\b"
        if re.search(pattern, location_norm) or re.search(pattern, title_lower):
            return exc
    return None


def _filter_settings() -> dict[str, Any]:
    f = get_filters_config()
    return {
        "inclusions": f.get("inclusions", _DEFAULT_INCLUSIONS),
        "seniority_exclusions": f.get("seniority_exclusions", _DEFAULT_SENIOR_EXCLUSIONS),
        "seniority_soft_exclusions": f.get("seniority_soft_exclusions", ["lead", "director"]),
        "seniority_soft_bypass_substrings": f.get(
            "seniority_soft_bypass_substrings", _DEFAULT_SOFT_BYPASS
        ),
        "level_exclusions": f.get("level_exclusions", LEVEL_EXCLUSIONS),
        "clearance_keywords": f.get("clearance_keywords", CLEARANCE_KEYWORDS),
        "unrelated_keywords": f.get("unrelated_keywords", UNRELATED_KEYWORDS),
        "unrelated_text_keywords": f.get("unrelated_text_keywords", UNRELATED_TEXT_KEYWORDS),
        "allowed_locations": f.get("allowed_locations", ALLOWED_LOCATIONS),
        "forbidden_locations": f.get("forbidden_locations", LOCATION_EXCLUSIONS),
    }


def _has_senior_in_title(title: str, cfg: dict[str, Any] | None = None) -> bool:
    """True if title should be excluded for seniority (strict + soft rules with bypass)."""
    title_lower = title.lower()
    fconf = cfg or _filter_settings()
    all_kw = fconf["seniority_exclusions"]
    soft = {x.strip().lower() for x in fconf["seniority_soft_exclusions"]}
    bypass = [b.lower() for b in fconf["seniority_soft_bypass_substrings"]]
    strict = [k for k in all_kw if k.lower() not in soft]

    for keyword in strict:
        if re.search(r"\b" + re.escape(keyword) + r"\b", title_lower):
            return True
    for keyword in soft:
        if re.search(r"\b" + re.escape(keyword) + r"\b", title_lower):
            if any(b in title_lower for b in bypass):
                continue
            return True
    return False


def _has_level_exclusion_in_title(title: str, level_exclusions: list[str]) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in level_exclusions)


def _has_clearance_in_text(text: str, clearance_keywords: list[str]) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in clearance_keywords)


def _has_unrelated_in_title(title: str, unrelated_keywords: list[str]) -> tuple[bool, str | None]:
    title_lower = title.lower()
    for keyword in unrelated_keywords:
        if re.search(r"\b" + re.escape(keyword) + r"\b", title_lower):
            return True, keyword
    return False, None


def _has_unrelated_in_text(text: str, unrelated_keywords: list[str]) -> tuple[bool, str | None]:
    text_lower = str(text or "").lower()
    if not text_lower:
        return False, None
    for keyword in unrelated_keywords:
        kw = str(keyword or "").strip().lower()
        if not kw:
            continue
        if " " in kw:
            if kw in text_lower:
                return True, keyword
            continue
        if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
            return True, keyword
    return False, None


def passes_sourcing_filter(job: dict, *, log_fn=None) -> tuple[bool, str]:
    """
    Rule-based filter for sourcing. Job must have keys: title, location, description.
    Returns (True, "") if job passes, (False, "reason") if excluded.
    """
    fs = _filter_settings()
    title = str(job.get("title", "")).lower()
    title_display = str(job.get("title", ""))
    location_raw = str(job.get("location", ""))
    location = normalize_sourcing_location(location_raw, title_display)
    desc = (str(job.get("description", "")) + " " + str(job.get("url", ""))).lower()

    title_inclusions = fs["inclusions"]

    found_match = False
    for inc in title_inclusions:
        if len(inc) <= 3:
            if re.search(r"\b" + re.escape(inc) + r"\b", title):
                found_match = True
                break
        elif inc.lower() in title:
            found_match = True
            break

    if not found_match:
        if "business" in title and "analyst" in title:
            found_match = True
        elif "product" in title and "manager" in title:
            found_match = True
        elif "product" in title and "director" in title:
            found_match = True
        elif "program" in title and "director" in title:
            found_match = True

    if not found_match:
        return False, "Title match fail"

    if any(marker in title for marker in TITLE_NON_US_MARKERS):
        return False, "Non-US marker in title"

    if _has_senior_in_title(title, fs):
        return False, "Seniority exclusion"

    if _has_level_exclusion_in_title(title, fs["level_exclusions"]):
        return False, "Intern/level exclusion"

    if not any(loc in location for loc in fs["allowed_locations"]):
        return False, "Location region mismatch"

    forbidden_hit = _forbidden_location_hits(location, title, fs["forbidden_locations"])
    if forbidden_hit:
        return False, f"Location exclusion ({forbidden_hit})"

    if _has_clearance_in_text(title + " " + desc, fs["clearance_keywords"]):
        return False, "Requires security clearance"

    has_unrelated, keyword = _has_unrelated_in_title(title, fs["unrelated_keywords"])
    if has_unrelated:
        return False, f"Unrelated field ({keyword})"
    has_unrelated_text, text_kw = _has_unrelated_in_text(desc, fs["unrelated_text_keywords"])
    if has_unrelated_text:
        return False, f"Unrelated field text ({text_kw})"

    s_cfg = get_sourcing_config()
    learned_phrases = load_learned_blocked_phrases_for_filter(sourcing_cfg=s_cfg)
    lb = learned_block_hit(str(job.get("title", "") or ""), learned_phrases)
    if lb:
        return False, f"Learned title block ({lb})"

    tf_cfg = get_title_fit_config()
    if tf_cfg.get("enabled"):
        snippet = str(job.get("description", "") or "")
        ok_tf, reason_tf, _ = evaluate_title_fit(
            str(job.get("title", "") or ""),
            snippet,
            title_fit_cfg=tf_cfg,
        )
        if not ok_tf:
            return False, reason_tf or "Title fit"

    return True, ""


def passes_evaluation_prefilter(job: dict) -> tuple[bool, str]:
    """
    Fast rule-based filter before LLM evaluation. Job should have keys:
    Role Title, Job Description, url (url used as fallback when JD is empty).
    """
    ts = str(job.get("Role Title", "") or job.get("title", ""))
    title = ts.lower()
    jd = str(job.get("Job Description", "") or job.get("description", "") or "")
    url = str(job.get("url", "") or job.get("Job Link", "") or "")
    text_for_clearance = (jd + " " + url).lower()
    fs = _filter_settings()

    if _has_senior_in_title(title, fs):
        return False, "Skip: Senior/Lead Role"

    if _has_clearance_in_text(title + " " + text_for_clearance, fs["clearance_keywords"]):
        return False, "Skip: Requires Security Clearance"

    has_unrelated, keyword = _has_unrelated_in_title(title, fs["unrelated_keywords"])
    if has_unrelated:
        return False, f"Skip: Unrelated Field ({keyword})"
    has_unrelated_text, text_kw = _has_unrelated_in_text(text_for_clearance, fs["unrelated_text_keywords"])
    if has_unrelated_text:
        return False, f"Skip: Unrelated Field Text ({text_kw})"

    tf_cfg = get_title_fit_config()
    if tf_cfg.get("enabled"):
        snippet = str(job.get("Job Description", "") or job.get("description", "") or "")
        ok_tf, reason_tf, _ = evaluate_title_fit(
            str(job.get("Role Title", "") or job.get("title", "") or ""),
            snippet,
            title_fit_cfg=tf_cfg,
        )
        if not ok_tf:
            return False, reason_tf or "Skip: Title fit"

    return True, ""


def filter_sourcing_jobs(jobs: list, log_each: bool = False) -> tuple[list, dict[str, int]]:
    """Apply passes_sourcing_filter to each job; return (passed, reject_reason_counts)."""
    out = []
    counts: Counter[str] = Counter()
    for job in jobs:
        passed, reason = passes_sourcing_filter(job)
        if passed:
            out.append(job)
        else:
            counts[reason] += 1
            if log_each:
                logging.info("Skipped: %s [%s]", reason, job.get("title", ""))
    return out, dict(counts)


def print_sourcing_filter_summary(
    static_rejects: dict[str, int],
    *,
    raw_count: int,
    after_static: int,
    ai_rejected: int = 0,
    saved_count: int = 0,
) -> None:
    """Single-line-friendly summary for operators and agents."""
    print("\n--- Sourcing filter summary ---")
    print(f"  Raw jobs in batch: {raw_count}")
    print(f"  Passed static filter: {after_static}")
    if static_rejects:
        learned_total = sum(
            n for r, n in static_rejects.items() if str(r).startswith("Learned title block")
        )
        if learned_total:
            print(f"  Rejected (Learned title blocks — all): {learned_total}")
        title_fit_total = sum(
            n for r, n in static_rejects.items() if str(r).startswith("Title fit")
        )
        if title_fit_total:
            print(f"  Rejected (Title fit — all reasons): {title_fit_total}")
        for reason, n in sorted(static_rejects.items(), key=lambda x: -x[1]):
            print(f"  Rejected ({reason}): {n}")
    if ai_rejected:
        print(f"  Rejected (AI sniffer): {ai_rejected}")
    print(f"  Proceeding to sheet/tagging: {saved_count}")
    print("--- End sourcing summary ---\n")
