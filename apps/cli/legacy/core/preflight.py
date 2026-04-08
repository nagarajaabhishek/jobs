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
) -> PreflightResult:
    """
    Fail-fast checks required to run one full daily cycle.

    Key product rule: evaluation MUST be grounded in the user's master context.
    If the compiled dense matrix is missing (or stale), we error out instead of guessing.
    """
    errors: List[str] = []
    warnings: List[str] = []

    # --- Environment / dependencies ---
    if require_gemini and not os.environ.get("GEMINI_API_KEY"):
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

    return PreflightResult(ok=(len(errors) == 0), errors=errors, warnings=warnings)

