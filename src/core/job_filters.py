"""
Shared job filter constants and logic for sourcing and evaluation.
Single source of truth so both pipelines stay in sync.
"""
from __future__ import annotations

import re
from src.core.config import get_filters_config

# Load dynamic filters
_f = get_filters_config()

# ----- Target roles (sourcing: title must match one of these) -----
TITLE_INCLUSIONS = _f.get("inclusions", [
    "product manager", "project manager", "program manager",
    "business analyst", "product owner", "scrum master",
    "agile coach", "gtm", "go-to market", "strategy", "operations analyst",
    "product lead", "project lead", "program lead", "delivery manager",
    "operations manager", "business operations", "chief of staff",
    "ba", "pm", "po", "tpm", "pmo", "scrum", "agile",
])

# ----- Exclusions (applied in both sourcing and evaluation) -----
SENIOR_KEYWORDS = _f.get("seniority_exclusions", [
    "senior", "sr", "sr.", "staff", "principal", "director",
    "vp", "head of", "lead", "manager ii",
])
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

# ----- Location (sourcing only) -----
ALLOWED_LOCATIONS = _f.get("allowed_locations", [
    "usa", "united states", "dubai", "uae", "remote", "us",
    ", al", ", ak", ", az", ", ar", ", ca", ", co", ", ct", ", de", ", fl", ", ga",
    ", hi", ", id", ", il", ", in", ", ia", ", ks", ", ky", ", la", ", me", ", md",
    ", ma", ", mi", ", mn", ", ms", ", mo", ", mt", ", ne", ", nv", ", nh", ", nj",
    ", nm", ", ny", ", nc", ", nd", ", oh", ", ok", ", or", ", pa", ", ri", ", sc",
    ", sd", ", tn", ", tx", ", ut", ", vt", ", va", ", wa", ", wv", ", wi", ", wy",
    ", dc"
])
LOCATION_EXCLUSIONS = _f.get("forbidden_locations", [
    "india", "uk", "london", "canada", "australia", "germany", "france",
    "singapore", "bangalore", "hyderabad", "toronto",
    "munich", "berlin", "dresden", "frankfurt", "europe",
])

# Non-US markers in title (sourcing)
TITLE_NON_US_MARKERS = ["(m/w/d)", "(all genders)"]


def _has_senior_in_title(title: str) -> bool:
    title_lower = title.lower()
    for keyword in SENIOR_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", title_lower):
            return True
    return False


def _has_level_exclusion_in_title(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in LEVEL_EXCLUSIONS)


def _has_clearance_in_text(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in CLEARANCE_KEYWORDS)


def _has_unrelated_in_title(title: str) -> tuple[bool, str | None]:
    title_lower = title.lower()
    for keyword in UNRELATED_KEYWORDS:
        if re.search(r"\b" + re.escape(keyword) + r"\b", title_lower):
            return True, keyword
    return False, None


def passes_sourcing_filter(job: dict, *, log_fn=None) -> tuple[bool, str]:
    """
    Rule-based filter for sourcing. Job must have keys: title, location, description.
    Returns (True, "") if job passes, (False, "reason") if excluded.
    """
    title = str(job.get("title", "")).lower()
    location = str(job.get("location", "")).lower()
    desc = (str(job.get("description", "")) + " " + str(job.get("url", ""))).lower()

    # Title must match target roles (with word boundary support for short codes)
    found_match = False
    for inc in TITLE_INCLUSIONS:
        if len(inc) <= 3: # Handle BA, PM, PO, TPM, PMO
            if re.search(r"\b" + re.escape(inc) + r"\b", title):
                found_match = True
                break
        elif inc in title: # Substring match for longer phrases like "product manager"
            found_match = True
            break
            
    if not found_match:
        # Special check for "Business Analyst" separated by words (e.g. "Business Systems Analyst")
        if "business" in title and "analyst" in title:
            found_match = True
        elif "product" in title and "manager" in title:
            found_match = True
            
    if not found_match:
        return False, "Title match fail"

    # Non-US markers in title
    if any(marker in title for marker in TITLE_NON_US_MARKERS):
        return False, "Non-US marker in title"

    # Senior/lead
    if _has_senior_in_title(title):
        return False, "Seniority exclusion"

    # Intern/student
    if _has_level_exclusion_in_title(title):
        return False, "Intern/level exclusion"

    # Location: must be in allowed regions
    if not any(loc in location for loc in ALLOWED_LOCATIONS):
        return False, "Location region mismatch"

    # Location: explicit exclusions (including in title for city names)
    for exc in LOCATION_EXCLUSIONS:
        if exc in location or exc in title:
            return False, f"Location exclusion ({exc})"

    # Clearance in title or description
    if _has_clearance_in_text(title + " " + desc):
        return False, "Requires security clearance"

    # Unrelated field in title
    has_unrelated, keyword = _has_unrelated_in_title(title)
    if has_unrelated:
        return False, f"Unrelated field ({keyword})"

    return True, ""


def passes_evaluation_prefilter(job: dict) -> tuple[bool, str]:
    """
    Fast rule-based filter before LLM evaluation. Job should have keys:
    Role Title, Job Description, url (url used as fallback when JD is empty).
    Returns (True, "") if job passes, (False, "reason") if excluded.
    """
    title = str(job.get("Role Title", "")).lower()
    jd = str(job.get("Job Description", "") or "")
    url = str(job.get("url", "") or job.get("Job Link", "") or "")
    text_for_clearance = (jd + " " + url).lower()

    if _has_senior_in_title(title):
        return False, "Skip: Senior/Lead Role"

    if _has_clearance_in_text(title + " " + text_for_clearance):
        return False, "Skip: Requires Security Clearance"

    has_unrelated, keyword = _has_unrelated_in_title(title)
    if has_unrelated:
        return False, f"Skip: Unrelated Field ({keyword})"

    return True, ""
