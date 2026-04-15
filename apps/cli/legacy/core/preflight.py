import os
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class PreflightResult:
    ok: bool
    errors: List[str]
    warnings: List[str]


def _mtime(path: str) -> Optional[float]:
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def _newer_than(target: str, sources: List[str]) -> Tuple[bool, List[str]]:
    """Return (is_newer, stale_sources). Missing sources are ignored here."""
    t_m = _mtime(target)
    if t_m is None:
        return False, []
    stale = []
    for s in sources:
        s_m = _mtime(s)
        if s_m is None:
            continue
        if s_m > t_m:
            stale.append(s)
    return len(stale) == 0, stale


def run_cycle_preflight(
    *,
    project_root: str,
    require_gemini: bool = True,
    require_google_credentials: bool = True,
    require_dense_profile: bool = True,
    check_title_fit_when_enabled: bool = True,
) -> PreflightResult:
    """
    Fail-fast checks required to run one full daily cycle.

    Key product rule: evaluation MUST be grounded in the user's master context.
    If the compiled dense matrix is missing (or stale), we error out instead of guessing.
    """
    errors: List[str] = []
    warnings: List[str] = []

    # --- Environment / dependencies ---
    eval_needs_gemini = True
    eval_needs_openrouter = False
    try:
        from apps.cli.legacy.core.config import get_evaluation_config

        _prov = (get_evaluation_config().get("provider") or "gemini").strip().lower()
        if _prov == "openai":
            eval_needs_gemini = False
        if _prov == "openrouter":
            eval_needs_gemini = False
            eval_needs_openrouter = True
    except Exception:
        pass

    if require_gemini and eval_needs_openrouter and not (
        os.environ.get("OPENROUTER_API_KEY") or ""
    ).strip():
        errors.append("Missing env var: OPENROUTER_API_KEY (evaluation.provider is openrouter)")

    if require_gemini and eval_needs_gemini and not os.environ.get("GEMINI_API_KEY"):
        errors.append("Missing env var: GEMINI_API_KEY")

    # --- Google credentials ---
    credentials_path = os.path.join(project_root, "config", "credentials.json")
    if require_google_credentials and not os.path.isfile(credentials_path):
        errors.append(f"Missing Google service account key: {credentials_path}")

    # --- Candidate profile prerequisites ---
    # Support development profile locations via env overrides.
    profiles_dir = os.environ.get("PROFILE_DIR") or os.path.join(project_root, "data", "profiles")
    master_context = os.environ.get("MASTER_PROFILE_PATH") or os.path.join(profiles_dir, "master_context.yaml")
    dense_matrix = os.environ.get("DENSE_MATRIX_PATH") or os.path.join(project_root, "data", "dense_master_matrix.json")

    if require_dense_profile:
        if not os.path.isfile(master_context):
            errors.append(
                "Missing master profile: data/profiles/master_context.yaml "
                "(this is the source of truth for evaluation context)."
            )
        if not os.path.isfile(dense_matrix):
            errors.append(
                "Missing compiled dense profile: data/dense_master_matrix.json. "
                "Generate it with: python3 apps/cli/scripts/tools/build_dense_matrix.py"
            )
        else:
            # If dense exists, ensure it's fresh vs master_context + role_*.yaml variants.
            role_variants = []
            if os.path.isdir(profiles_dir):
                for fn in os.listdir(profiles_dir):
                    if fn.startswith("role_") and fn.endswith(".yaml"):
                        role_variants.append(os.path.join(profiles_dir, fn))
            sources = [master_context] + role_variants
            ok, stale = _newer_than(dense_matrix, sources)
            if not ok and stale:
                stale_rel = [os.path.relpath(p, project_root) for p in stale]
                errors.append(
                    "Dense profile is stale (source profile changed after it was compiled). "
                    "Rebuild with: python3 apps/cli/scripts/tools/build_dense_matrix.py. "
                    f"Newer inputs: {', '.join(stale_rel)}"
                )

    # --- Title & seniority fit (must be valid before sourcing/eval when enabled) ---
    if check_title_fit_when_enabled:
        try:
            from apps.cli.legacy.core.config import get_title_fit_config
            from apps.cli.legacy.core import title_fit_gate as tft
        except ImportError as e:
            errors.append(f"Title fit preflight import failed: {e}")
        else:
            tf_cfg = get_title_fit_config()
            if tf_cfg.get("enabled"):
                tf_path = tft.title_fit_user_yaml_path(project_root)
                if not os.path.isfile(tf_path):
                    errors.append(
                        "title_fit.enabled is true but title_fit_user.yaml is missing. "
                        f"Expected file: {tf_path}. "
                        "Create it (see data/profiles/title_fit_user.yaml) or set title_fit.enabled: false in config/pipeline.yaml."
                    )
                tracks = tft.load_all_track_definitions(project_root)
                if not tracks:
                    errors.append(
                        "title_fit.enabled but no track definitions were found. "
                        "Add YAML files under config/title_fit/tracks/ with an `id` field."
                    )
                if os.path.isfile(tf_path):
                    user = tft.load_title_fit_user_config(project_root)
                    if not user:
                        errors.append(
                            f"title_fit_user.yaml at {tf_path} is empty or invalid (could not load as a mapping)."
                        )
                    else:
                        active = [
                            str(x).strip()
                            for x in (user.get("active_tracks") or [])
                            if str(x).strip()
                        ]
                        if not active:
                            errors.append(
                                "title_fit.enabled: title_fit_user.yaml must set active_tracks to a non-empty list."
                            )
                        for tid in active:
                            if tid not in tracks:
                                errors.append(
                                    f"title_fit: unknown track id {tid!r} in active_tracks "
                                    "(no config/title_fit/tracks/*.yaml with this id)."
                                )
                if tf_cfg.get("llm_disambiguation_enabled") and require_gemini:
                    if eval_needs_openrouter and not (
                        os.environ.get("OPENROUTER_API_KEY") or ""
                    ).strip():
                        errors.append(
                            "title_fit.llm_disambiguation_enabled is true but OPENROUTER_API_KEY is not set "
                            "(evaluation.provider is openrouter)."
                        )
                    elif eval_needs_gemini and not os.environ.get("GEMINI_API_KEY"):
                        errors.append(
                            "title_fit.llm_disambiguation_enabled is true but GEMINI_API_KEY is not set."
                        )
                    elif (
                        not eval_needs_gemini
                        and not eval_needs_openrouter
                        and not (os.environ.get("OPENAI_API_KEY") or "").strip()
                    ):
                        errors.append(
                            "title_fit.llm_disambiguation_enabled is true but OPENAI_API_KEY is not set "
                            "(evaluation.provider is openai)."
                        )

    # --- Learned sourcing blocks (optional) ---
    try:
        from apps.cli.legacy.core.config import get_sourcing_config

        s_cfg = get_sourcing_config()
        if s_cfg.get("apply_learned_title_blocks"):
            rel = s_cfg.get("learned_title_blocks_path", "data/sourcing_learned_title_blocks.yaml")
            lb_path = rel if os.path.isabs(rel) else os.path.join(project_root, rel)
            if not os.path.isfile(lb_path):
                errors.append(
                    "sourcing.apply_learned_title_blocks is true but learned title blocks file is missing. "
                    f"Expected: {lb_path}. Run: python3 apps/cli/scripts/tools/learn_sourcing_filters_from_sheet.py"
                )
    except Exception as e:
        errors.append(f"Learned sourcing blocks preflight error: {e}")

    return PreflightResult(ok=(len(errors) == 0), errors=errors, warnings=warnings)

