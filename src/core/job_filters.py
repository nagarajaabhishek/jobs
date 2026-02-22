"""
Shared job filter constants and logic for sourcing and evaluation.
Single source of truth so both pipelines stay in sync.
"""
from __future__ import annotations

import re

# ----- Target roles (sourcing: title must match one of these) -----
TITLE_INCLUSIONS = [
    "product manager", "project manager", "program manager",
    "business analyst", "product owner", "scrum master",
    "agile coach", "gtm", "go-to market", "strategy", "operations analyst",
]

# ----- Exclusions (applied in both sourcing and evaluation) -----
SENIOR_KEYWORDS = [
    "senior", "sr", "sr.", "staff", "principal", "director",
    "vp", "head of", "lead", "manager ii",
]
LEVEL_EXCLUSIONS = [
    "intern", "internship", "co-op", "graduate intern", "student intern",
]
CLEARANCE_KEYWORDS = [
    "clearance", "ts/sci", "secret clearance", "top secret",
]
UNRELATED_KEYWORDS = [
    "nurse", "registered nurse", "rn", "physician", "driver", "cdl",
    "warehouse", "mechanic", "cashier", "architect", "software engineer",
    "backend", "frontend", "fullstack", "full stack", "account executive", "recruiter",
    "firmware", "hardware", "validation", "characterization",
    "testing engineer", "product engineer", "data analyst",
]

# ----- Location (sourcing only) -----
ALLOWED_LOCATIONS = ["usa", "united states", "dubai", "uae", "remote", "us"]
LOCATION_EXCLUSIONS = [
    "india", "uk", "london", "canada", "australia", "germany", "france",
    "singapore", "bangalore", "hyderabad", "toronto",
    "munich", "berlin", "dresden", "frankfurt", "europe",
]

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

    # Title must match target roles
    if not any(inc in title for inc in TITLE_INCLUSIONS):
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
