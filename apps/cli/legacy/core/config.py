"""Load pipeline config from config/pipeline.yaml (optional)."""
import copy
import os
import yaml
from datetime import datetime, timedelta

_default = {
    "sourcing": {
        "queries": [
            "Product Manager", "Project Manager", "Program Manager",
            "Business Analyst", "Product Owner", "Scrum Master",
            "Strategy Operations", "GTM Manager",
        ],
        "locations": {
            "United States": 80,
            "Dubai": 20,
            "Remote": 50
        },
        "max_workers": 4,
        "use_ai_filter": False,
        "jobspy_sites": ["linkedin", "indeed", "google", "zip_recruiter"],
        "ats_boards": {
            "greenhouse": ["canva", "discord", "figma"],
            "lever": ["netflix", "palantir", "discord"],
            "ashby": ["ashby", "notion", "figma", "linear", "vercel", "ramp"],
        },
        # Mined from sheet history (see learn_sourcing_filters_from_sheet.py). Off until you review YAML.
        "apply_learned_title_blocks": False,
        "learned_title_blocks_path": "data/sourcing_learned_title_blocks.yaml",
        # github.com/jobright-ai README job tables only; [] disables Jobright GitHub sourcing.
        "jobright_github_repos": [
            "2026-Product-Management-Internship",
            "2026-Product-Management-New-Grad",
            "2026-Business-Analyst-Internship",
            "2026-Business-Analyst-New-Grad",
            "Daily-H1B-Jobs-In-Tech",
        ],
        # When true, run Jobright README feeds first, then JobSpy loop; final community pass skips Jobright.
        "run_jobright_first": True,
        # Max JobSpy interleaved iterations before giving up on target_count (was hardcoded 10).
        "interleaved_max_iterations": 10,
        # After Jobright scrape, run up to N evaluate_all(NEW, limit=evaluation.limit) waves before JobSpy.
        "jobright_eval_max_waves": 1,
        # Optional public ATS endpoint slugs added to once-per-cycle community phase.
        "run_smartrecruiters_once": False,
        "smartrecruiters_companies": [],
        "run_recruitee_once": False,
        "recruitee_companies": [],
    },
    "evaluation": {
        "provider": "gemini",
        "gemini_model": "gemini-1.5-pro-latest",
        # OpenRouter (provider: openrouter): OpenAI-compatible API, OPENROUTER_API_KEY. Verify slugs on openrouter.ai.
        "openrouter_model": "google/gemini-2.5-flash",
        "openrouter_fallback_model": "openai/gpt-4o-mini",
        "openrouter_site_url": "",
        "openrouter_app_name": "Job Automation",
        # If primary Gemini fails: openai_then_gemma (OpenAI then hosted Gemma), or openai / gemma / gemma_then_openai.
        # If provider is openrouter: use openrouter_fallback (second model) or none.
        "fallback_provider": "openai_then_gemma",
        "openrouter_fast_fallback": True,
        "openai_model": "gpt-4o-mini",
        # Hosted Gemma on the same Gemini API (same GEMINI_API_KEY). Docs: ai.google.dev/gemma/docs/core/gemma_on_gemini_api
        "gemma_model": "gemma-4-31b-it",
        "sourcing_model": "gemini-2.5-flash",
        "batch_eval_size": 3,
        "sheet_batch_size": 25,
        "limit": 300,
        # Cap JD chars per job in multi-job LLM calls (0 = no cap). Prevents truncation → NEEDS_REVIEW.
        "batch_jd_max_chars": 12000,
        # Optional token-saver: before LLM call, compute deterministic fallback score and skip
        # rows below this threshold (0 disables). Example: 70 means "don't spend LLM tokens < 70".
        "skip_llm_if_fallback_below": 0,
        # First pass prompt compaction: send JD snippet first, then retry full JD only for gray-zone scores.
        "snippet_first_enabled": False,
        "snippet_first_chars": 2200,
        "gray_zone_full_jd_retry": True,
        "gray_zone_min_score": 68,
        "gray_zone_max_score": 82,
        # Provider stickiness: after repeated Gemini misses, temporarily run OpenAI first.
        "provider_stickiness_enabled": False,
        "provider_stickiness_failures": 2,
        "provider_stickiness_calls": 20,
        # Optional second LLM pass via LLMRouter (off by default).
        "deep_eval_enabled": False,
        "deep_eval_min_score": 90,
        # Write data/tailor_payloads/<date>_row<n>.json for high conviction rows (off by default).
        "export_tailor_json": False,
        # Resume tailoring candidate threshold (used by pipeline tailor phase + tailor payload export).
        "tailor_min_score": 90,
        # Flush evaluated rows to Sheets after this many completed jobs (2–10; project SOP recommends 2–5).
        "sheet_sync_every_n_evals": 3,
        # On Gemini HTTP 429, skip long Gemini retries and use fallback_provider (e.g. OpenAI) if configured.
        "gemini_429_fast_openai_fallback": True,
        # On OpenRouter primary HTTP 429, skip retries and try openrouter_fallback_model (if configured).
        "openrouter_fast_fallback": True,
        # Optional end-of-cycle sweeps (run_pipeline.py) to clean up retryable failures.
        "run_needs_review_sweep": False,
        "needs_review_sweep_limit": 200,
        "run_llm_failed_sweep": False,
        "llm_failed_sweep_limit": 200,
        # If true, keep looping end-of-cycle eval until NEW/NEEDS_REVIEW/LLM_FAILED are drained (or max passes reached).
        "enforce_clean_sheet_before_finish": False,
        "clean_sheet_pass_limit": 300,
        "clean_sheet_max_passes": 6,
        # End gates (run_pipeline.py): when true, fail/stop the cycle if these are not met.
        "require_target_count_before_finish": False,
        "require_clean_sheet_before_finish": False,
    },
    "learning": {
        "enabled": True,
        "max_abs_delta": 15,
        "patterns_path": "data/learned_patterns.yaml",
    },
    "digest": {
        "enabled": True,
        "top_n": 20,
        "output_dir": "data/digests",
    },
    "cycle": {
        "run_digest_after_pipeline": True,
        "run_feedback_ingest": False,
        "automation_hooks_enabled": False,
        # Auto-mine title block phrases from sheet outcomes after each cycle.
        "run_filter_learning": False,
        "filter_learning_output": "data/sourcing_learned_title_blocks.yaml",
        "filter_learning_neg_max_score": 65,
        "filter_learning_pos_min_score": 80,
        "filter_learning_min_neg_count": 3,
        "filter_learning_min_lift": 2.0,
        "filter_learning_max_phrases": 100,
        "filter_learning_dry_run": False,
        # Rank sources/companies from recent dated tabs (no LLM). Writes YAML for manual review.
        "run_sourcing_hints": False,
        "sourcing_hints_output": "data/sourcing_hints.yaml",
        "sourcing_hints_recent_tabs": 21,
        "sourcing_hints_tab_filter": "",
        "sourcing_hints_thr_70": 70.0,
        "sourcing_hints_thr_80": 80.0,
        "sourcing_hints_min_rows_per_source": 5,
        "sourcing_hints_top_sources": 25,
        "sourcing_hints_top_companies": 40,
        "sourcing_hints_quiet": True,
    },
    "sheet": {
        # Paste full URL or raw ID to bind an existing workbook (avoids Drive create / quota issues).
        "spreadsheet_id": None,
        # Daily tab name is YYYY-MM-DD. Use "today", "yesterday" (e.g. run just after midnight on laptop),
        # or "fixed" with worksheet_tab_date_fixed. Override anytime: SHEET_TAB_DATE=2026-04-09
        "worksheet_tab_date_mode": "today",
        "worksheet_tab_date_fixed": None,
        # Same workbook: optional tab to paste JD URLs for tailoring (ensure_manual_jd_tailor_worksheet).
        "manual_jd_tailor_tab": "Manual_JD_Tailor",
    },
    "local_store": {
        # SQLite outbox when Google Sheets append/update fails after retries (see sheet_outbox.py).
        "enabled": False,
        "db_path": "data/pipeline_outbox.db",
    },
    "title_fit": {
        "enabled": False,
        "require_track_match": True,
        "llm_disambiguation_enabled": False,
        "ambiguous_default": "reject",
        "snippet_max_chars": 1200,
        "disambiguation_model": None,
    },
    # Resume tailoring (TailorAgent, tailor_from_urls.py): profile folder under .agent/data/<profile>/
    "resume": {
        "profile": "Abhishek",
        "base_role_yaml": "role_product_ops.yaml",
        "agent_dir": "core_agents/resume_agent/.agent",
    },
}


def load_pipeline_config():
    """Load config from config/pipeline.yaml. Falls back to defaults if missing."""
    path = os.environ.get("PIPELINE_CONFIG")
    if not path:
        path = os.path.join(os.getcwd(), "config", "pipeline.yaml")
    if not os.path.isfile(path):
        return _default
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
        
        # Merge logical blocks
        out = _default.copy()
        for key in (
            "sourcing",
            "evaluation",
            "filters",
            "learning",
            "digest",
            "cycle",
            "sheet",
            "local_store",
            "title_fit",
            "resume",
        ):
            if key in data:
                # If it's a dict, merge it. If it's a list (unlikely here but safety), replace it.
                if isinstance(_default.get(key), dict) and isinstance(data[key], dict):
                    out[key] = {**_default.get(key, {}), **data[key]}
                else:
                    out[key] = data[key]
            elif key not in out:
                out[key] = {}
        return out
    except Exception:
        return _default


def _merge_portal_seeds_into_sourcing(sourcing_dict):
    """Extend ats_boards slugs from config/portal_seeds.yml (career-ops–style seed list)."""
    if not isinstance(sourcing_dict, dict):
        return sourcing_dict
    path = os.path.join(os.getcwd(), "config", "portal_seeds.yml")
    if not os.path.isfile(path):
        return sourcing_dict
    try:
        with open(path, "r", encoding="utf-8") as f:
            seeds = yaml.safe_load(f) or {}
    except Exception:
        return sourcing_dict
    seed_ats = (seeds.get("ats_boards") or {}) if isinstance(seeds, dict) else {}
    ats = dict(sourcing_dict.get("ats_boards") or {})
    for key in ("greenhouse", "lever", "ashby"):
        base = [str(x).strip() for x in (ats.get(key) or []) if str(x).strip()]
        extra = [str(x).strip() for x in (seed_ats.get(key) or []) if str(x).strip()]
        seen = set()
        merged = []
        for x in base + extra:
            low = x.lower()
            if low not in seen:
                seen.add(low)
                merged.append(x)
        ats[key] = merged
    out = dict(sourcing_dict)
    out["ats_boards"] = ats
    return out


def get_sourcing_config():
    base = load_pipeline_config().get("sourcing", _default["sourcing"])
    merged = _merge_portal_seeds_into_sourcing(copy.deepcopy(base))
    return merged


def get_evaluation_config():
    return load_pipeline_config().get("evaluation", _default["evaluation"])


def get_filters_config():
    """Returns the filters section for dynamic loading in job_filters.py."""
    return load_pipeline_config().get("filters", {})


def get_learning_config():
    return load_pipeline_config().get("learning", _default.get("learning", {}))


def get_digest_config():
    return load_pipeline_config().get("digest", _default.get("digest", {}))


def get_cycle_config():
    return load_pipeline_config().get("cycle", _default.get("cycle", {}))


def get_sheet_config():
    return load_pipeline_config().get("sheet", _default.get("sheet", {}))


def get_local_store_config():
    """local_store: SQLite outbox for failed Sheet writes (enabled, db_path)."""
    return load_pipeline_config().get("local_store", _default.get("local_store", {}))


def get_worksheet_tab_date() -> str:
    """
    Tab title for the daily worksheet (YYYY-MM-DD).

    Priority:
      1. Env SHEET_TAB_DATE or WORKSHEET_TAB_DATE (explicit date)
      2. Env SHEET_TAB_DATE_MODE: yesterday | fixed | today
      3. Env SHEET_TAB_DATE_FIXED (used when mode=fixed)
      4. sheet.worksheet_tab_date_mode: yesterday | fixed | today
      5. Local date today
    """
    env_raw = (os.environ.get("SHEET_TAB_DATE") or os.environ.get("WORKSHEET_TAB_DATE") or "").strip()
    if env_raw:
        return env_raw[:10]

    cfg = get_sheet_config()
    env_mode = (os.environ.get("SHEET_TAB_DATE_MODE") or "").strip().lower()
    mode = env_mode or str(cfg.get("worksheet_tab_date_mode") or "today").strip().lower()
    if mode == "yesterday":
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    if mode == "fixed":
        fixed = (os.environ.get("SHEET_TAB_DATE_FIXED") or "").strip() or cfg.get("worksheet_tab_date_fixed")
        if fixed and str(fixed).strip():
            return str(fixed).strip()[:10]
    return datetime.now().strftime("%Y-%m-%d")


def get_title_fit_config():
    return load_pipeline_config().get("title_fit", _default.get("title_fit", {}))


def get_resume_config():
    """Paths for TailorAgent: profile name + base role YAML under agent_dir/data/<profile>/."""
    return load_pipeline_config().get("resume", _default.get("resume", {}))
