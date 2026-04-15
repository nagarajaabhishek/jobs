"""Fetch JD text into config/jd_cache.json for arbitrary job URLs (eval / tailoring)."""
from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient


def ensure_jd_cached(client: "GoogleSheetsClient", url: str, *, project_root: str | None = None) -> tuple[bool, str]:
    """
    If `url` is missing from jd_cache (or empty), run SourcingAgent manual JD fetch and save.
    Returns (ok, message).
    """
    from apps.cli.legacy.core.google_sheets_client import normalize_job_url
    from core_agents.sourcing_agent.agent import SourcingAgent

    root = project_root or os.getcwd()
    if root not in sys.path:
        sys.path.insert(0, root)

    canon = normalize_job_url(url)
    if not canon:
        return False, "empty or invalid URL"
    existing = (client.get_jd_for_url(url) or "").strip()
    if existing and existing.lower() != "none":
        return True, f"cache hit ({len(existing)} chars)"
    agent = SourcingAgent(client)
    desc, ok, method = agent._fetch_jd_manually(url)
    if not ok or not (desc or "").strip():
        return False, f"JD fetch failed ({method})"
    cache = client._load_jd_cache()
    cache[canon] = {
        "jd": desc.strip()[:50000],
        "timestamp": datetime.now().strftime("%Y-%m-%d"),
    }
    client._save_jd_cache(cache)
    return True, f"fetched via {method} ({len(desc)} chars)"
