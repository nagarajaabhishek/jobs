"""
Profile-driven title and seniority gate (multi-track). Used by sourcing and eval prefilter.
"""
from __future__ import annotations

import glob
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)

# Stripped from track YAML unless user sets include_internship_entry_signals: true
_INTERN_PREFER_TOKENS = ("intern", "internship")

TRACK_STRICT_FLAG_KEY = {
    "product_management": "has_titled_pm_role",
    "business_analysis": "has_titled_ba_role",
    "program_project_management": "has_titled_program_project_role",
}


def _project_root(explicit: Optional[str] = None) -> str:
    """Repository root for config paths. Use explicit when preflight runs before cwd is guaranteed."""
    if explicit and str(explicit).strip():
        return str(explicit).strip()
    return os.getcwd()


def _profiles_dir(project_root: Optional[str] = None) -> str:
    pd = os.environ.get("PROFILE_DIR")
    if pd:
        return pd
    return os.path.join(_project_root(project_root), "data", "profiles")


def title_fit_user_yaml_path(project_root: Optional[str] = None) -> str:
    root = _project_root(project_root)
    master = os.environ.get("MASTER_PROFILE_PATH")
    if master:
        mp = master if os.path.isabs(master) else os.path.normpath(os.path.join(root, master))
        if os.path.isfile(mp):
            candidate = os.path.join(os.path.dirname(os.path.abspath(mp)), "title_fit_user.yaml")
            if os.path.isfile(candidate):
                return candidate
    return os.path.join(_profiles_dir(project_root), "title_fit_user.yaml")


def tracks_dir(project_root: Optional[str] = None) -> str:
    return os.path.join(_project_root(project_root), "config", "title_fit", "tracks")


def load_title_fit_user_config(project_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    path = title_fit_user_yaml_path(project_root)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data if isinstance(data, dict) else None
    except OSError:
        return None


def effective_yoe_from_profile(user: Dict[str, Any]) -> Optional[float]:
    if user.get("effective_yoe") is not None:
        try:
            return float(user["effective_yoe"])
        except (TypeError, ValueError):
            pass
    matrix_path = os.path.join(_project_root(), "data", "dense_master_matrix.json")
    if os.path.isfile(matrix_path):
        try:
            with open(matrix_path, "r", encoding="utf-8") as f:
                m = json.load(f)
            gt = (m or {}).get("global_traits") or {}
            y = gt.get("years_of_experience")
            if y is not None:
                return float(y)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    return None


def load_all_track_definitions(project_root: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    pattern = os.path.join(tracks_dir(project_root), "*.yaml")
    for path in sorted(glob.glob(pattern)):
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
            if not isinstance(raw, dict):
                continue
            tid = str(raw.get("id") or "").strip()
            if tid:
                out[tid] = raw
        except OSError:
            continue
    return out


def merge_track_with_user_overrides(
    track: Dict[str, Any], user: Dict[str, Any]
) -> Dict[str, Any]:
    t = dict(track)
    extra_b = [str(x).strip().lower() for x in (user.get("extra_block_tokens") or []) if str(x).strip()]
    extra_p = [str(x).strip().lower() for x in (user.get("extra_prefer_tokens") or []) if str(x).strip()]
    t["block_title_tokens"] = list(
        dict.fromkeys([str(x).lower() for x in (t.get("block_title_tokens") or [])] + extra_b)
    )
    base_prefer = [str(x).lower() for x in (t.get("prefer_title_tokens") or [])]
    merged_prefer = list(dict.fromkeys(base_prefer + extra_p))
    intern_on = bool(user.get("include_internship_entry_signals"))
    if intern_on:
        for tok in _INTERN_PREFER_TOKENS:
            if tok not in merged_prefer:
                merged_prefer.append(tok)
    else:
        merged_prefer = [x for x in merged_prefer if x not in _INTERN_PREFER_TOKENS]
    t["prefer_title_tokens"] = merged_prefer
    return t


def _title_matches_track(title_lower: str, patterns: List[str]) -> bool:
    for p in patterns:
        s = str(p).strip().lower()
        if not s:
            continue
        if s.startswith("regex:"):
            try:
                if re.search(s[6:].strip(), title_lower, re.IGNORECASE):
                    return True
            except re.error:
                continue
        elif s in title_lower:
            return True
    return False


def _match_score(title_lower: str, patterns: List[str]) -> int:
    n = 0
    for p in patterns:
        s = str(p).strip().lower()
        if not s:
            continue
        if s.startswith("regex:"):
            try:
                if re.search(s[6:].strip(), title_lower, re.IGNORECASE):
                    n += 1
            except re.error:
                continue
        elif s in title_lower:
            n += 1
    return n


def pick_best_track(
    title_lower: str,
    active_tracks: List[str],
    all_tracks: Dict[str, Dict[str, Any]],
) -> Optional[str]:
    best_id: Optional[str] = None
    best_score = 0
    for tid in active_tracks:
        t = all_tracks.get(tid)
        if not t:
            continue
        patterns = t.get("title_match") or []
        sc = _match_score(title_lower, patterns)
        if sc > best_score:
            best_score = sc
            best_id = tid
    return best_id


def _word_or_phrase_in_title(title_lower: str, token: str) -> bool:
    tok = token.strip().lower()
    if not tok:
        return False
    if " " in tok:
        return tok in title_lower
    return bool(re.search(r"\b" + re.escape(tok) + r"\b", title_lower))


def _has_any_block(title_lower: str, tokens: List[str]) -> Optional[str]:
    for tok in tokens:
        if _word_or_phrase_in_title(title_lower, str(tok)):
            return str(tok)
    return None


def _has_prefer_signal(title_lower: str, tokens: List[str]) -> bool:
    for tok in tokens:
        if _word_or_phrase_in_title(title_lower, str(tok)):
            return True
    return False


def _has_ambiguous_signal(title_lower: str, tokens: List[str]) -> bool:
    for tok in tokens:
        if _word_or_phrase_in_title(title_lower, str(tok)):
            return True
    return False


def _max_required_yoe_from_text(text: str, patterns: List[str]) -> Optional[int]:
    best: Optional[int] = None
    for pat in patterns:
        try:
            for m in re.finditer(str(pat), text, re.IGNORECASE):
                g = m.groups()
                if g:
                    try:
                        val = int(g[0])
                        best = max(best or 0, val)
                    except ValueError:
                        continue
        except re.error:
            continue
    return best


def _strict_entry_violation(
    title_lower: str,
    track: Dict[str, Any],
    user: Dict[str, Any],
    track_id: str,
) -> bool:
    subs = track.get("strict_entry_substrings_when_untitled_pm") or []
    if not subs:
        return False
    flag_key = TRACK_STRICT_FLAG_KEY.get(track_id)
    if not flag_key:
        return False
    flags = user.get("first_formal_role_flags") or {}
    if flags.get(flag_key, True):
        return False
    hit_plain = any(s.strip().lower() in title_lower for s in subs if str(s).strip())
    if not hit_plain:
        return False
    prefer = track.get("prefer_title_tokens") or []
    if _has_prefer_signal(title_lower, prefer):
        return False
    return True


def _llm_disambiguate(
    title: str,
    snippet: str,
    track: Dict[str, Any],
    user: Dict[str, Any],
    yoe: Optional[float],
    model: Optional[str],
) -> Tuple[bool, str]:
    try:
        from apps.cli.legacy.core.llm_router import LLMRouter
    except ImportError:
        return False, "LLM import failed"

    system = (
        "You classify whether a job title is appropriate for the candidate's seniority. "
        "Return ONLY one JSON object: "
        '{"verdict":"pass"|"reject","reason":"short string"}'
    )
    user_blob = json.dumps(
        {
            "title": title,
            "snippet": (snippet or "")[:800],
            "track": track.get("display_name", track.get("id")),
            "effective_yoe": yoe,
            "policy": user.get("policy", "conservative"),
            "flags": user.get("first_formal_role_flags") or {},
        },
        ensure_ascii=False,
    )
    fmt = "\n\nReturn ONLY valid JSON, no markdown fences."
    raw, engine = LLMRouter().generate_content(system, user_blob, formatting_instruction=fmt, model=model)
    if engine == "FAILED" or not (raw or "").strip():
        return False, "LLM failed"
    t = raw.strip()
    a = t.find("{")
    b = t.rfind("}")
    if a == -1 or b <= a:
        return False, "LLM JSON missing"
    try:
        obj = json.loads(t[a : b + 1])
        v = str(obj.get("verdict", "")).lower().strip()
        r = str(obj.get("reason", "")).strip()
        if v == "pass":
            return True, r or "LLM pass"
        return False, r or "LLM reject"
    except json.JSONDecodeError:
        return False, "LLM parse error"


def evaluate_title_fit(
    title: str,
    snippet: str,
    *,
    title_fit_cfg: Dict[str, Any],
    user: Optional[Dict[str, Any]] = None,
    all_tracks: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Returns (passed, reason, detail_dict).
    """
    detail: Dict[str, Any] = {}
    if not title_fit_cfg.get("enabled", False):
        return True, "", {"skipped": "disabled"}

    user = user if user is not None else load_title_fit_user_config()
    if user is None:
        logger.warning(
            "title_fit.enabled but no title_fit_user.yaml at %s — skipping gate.",
            title_fit_user_yaml_path(),
        )
        return True, "", {"skipped": "no_user_file"}

    all_tracks = all_tracks if all_tracks is not None else load_all_track_definitions()
    active = [str(x).strip() for x in (user.get("active_tracks") or []) if str(x).strip()]
    if not active:
        logger.warning("title_fit: active_tracks empty — skipping gate.")
        return True, "", {"skipped": "no_active_tracks"}

    title_lower = str(title or "").lower().strip()
    snip = str(snippet or "")[: int(title_fit_cfg.get("snippet_max_chars", 1200))]
    combined = (title_lower + " " + snip.lower()).strip()

    best = pick_best_track(title_lower, active, all_tracks)
    require = bool(title_fit_cfg.get("require_track_match", True))
    if not best:
        if require:
            return False, "Title fit: no matching track", {"track": None}
        return True, "", {"track": None, "note": "no_track_match_allowed"}

    base_track = all_tracks.get(best) or {}
    track = merge_track_with_user_overrides(base_track, user)
    detail["track_id"] = best

    blk = _has_any_block(title_lower, list(track.get("block_title_tokens") or []))
    if blk:
        return False, f"Title fit: blocked token ({blk})", detail

    yoe = effective_yoe_from_profile(user)
    detail["effective_yoe"] = yoe
    patterns = list(track.get("min_yoe_patterns") or [])
    req_yoe = _max_required_yoe_from_text(combined, patterns)
    if req_yoe is not None and yoe is not None:
        slack = float(track.get("slack_years_above_required", 1.0) or 0.0)
        if req_yoe > yoe + slack:
            return False, f"Title fit: requires ~{req_yoe}+ YOE (you: {yoe})", detail

    if _strict_entry_violation(title_lower, track, user, best):
        return False, "Title fit: plain title without entry signal", detail

    amb_tokens = list(track.get("ambiguous_title_tokens") or [])
    policy = str(user.get("policy", "conservative")).lower().strip()
    ambiguous_hit = _has_ambiguous_signal(title_lower, amb_tokens)

    if ambiguous_hit:
        if title_fit_cfg.get("llm_disambiguation_enabled"):
            from apps.cli.legacy.core.config import get_evaluation_config

            eval_cfg = get_evaluation_config()
            mdl = title_fit_cfg.get("disambiguation_model") or eval_cfg.get(
                "sourcing_model"
            ) or eval_cfg.get("gemini_model")
            ok, why = _llm_disambiguate(title, snip, track, user, yoe, mdl)
            detail["llm_disambiguation"] = why
            if ok:
                return True, "", detail
            return False, f"Title fit: {why}", detail

        if policy == "aggressive":
            return True, "", detail
        if policy == "conservative":
            return False, "Title fit: ambiguous title (conservative; enable LLM or relax policy)", detail
        default = str(title_fit_cfg.get("ambiguous_default", "reject")).lower()
        if default == "pass":
            return True, "", detail
        return False, "Title fit: ambiguous seniority in title", detail

    return True, "", detail


def sniffer_role_bullet_text(user: Optional[Dict[str, Any]] = None) -> str:
    """Build dynamic role list text for ai_sniff_relevance."""
    user = user or load_title_fit_user_config()
    if not user:
        return (
            "Product Manager, Project Manager, Program Manager, Business Analyst, "
            "Product Owner, Scrum Master, or GTM/Strategy Operations"
        )
    active = [str(x).strip() for x in (user.get("active_tracks") or []) if str(x).strip()]
    all_t = load_all_track_definitions()
    names = []
    for tid in active:
        t = all_t.get(tid) or {}
        dn = str(t.get("display_name") or tid).strip()
        if dn:
            names.append(dn)
    if not names:
        return (
            "Product Manager, Project Manager, Program Manager, Business Analyst, "
            "Product Owner, Scrum Master, or GTM/Strategy Operations"
        )
    return ", ".join(names)


def sniffer_constraints_paragraph(user: Optional[Dict[str, Any]] = None) -> str:
    user = user or load_title_fit_user_config()
    yoe = effective_yoe_from_profile(user or {})
    flags = (user or {}).get("first_formal_role_flags") or {}
    intern_scope = bool((user or {}).get("include_internship_entry_signals"))
    lines = [
        f"Candidate effective YOE (approx): {yoe if yoe is not None else 'unknown'}. "
        "Reject if the role strictly demands much more seniority than this.",
        f"Role flags (honor literally): {json.dumps(flags, ensure_ascii=False)}.",
        f"Internship counts toward YOE: {(user or {}).get('count_internship_toward_yoe', True)}.",
        f"User is actively including internship postings in this search: {intern_scope}.",
    ]
    return " ".join(lines)
