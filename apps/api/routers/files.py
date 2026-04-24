"""Serve tailored resume files from paths stored in Sheets (project-root only)."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from apps.api.paths import PROJECT_ROOT

router = APIRouter()


def _resolve_under_root(raw: str) -> Path:
    raw = unquote(raw or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Missing path")
    root = Path(PROJECT_ROOT).resolve()
    candidate = Path(os.path.expanduser(raw))
    if not candidate.is_absolute():
        candidate = (root / raw).resolve()
    else:
        candidate = candidate.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as e:
        raise HTTPException(status_code=403, detail="Path must stay under project root") from e
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return candidate


@router.get("/files/resume")
def serve_resume(
    path: str = Query(..., description="Absolute path under repo root, or path relative to repo root"),
) -> FileResponse:
    p = _resolve_under_root(path)
    media = "application/pdf" if p.suffix.lower() == ".pdf" else "text/plain"
    if p.suffix.lower() in (".tex", ".yaml", ".yml", ".md"):
        media = "text/plain"
    return FileResponse(p, media_type=media, filename=p.name)


@router.get("/files/exists")
def file_exists(path: str = Query(...)) -> dict:
    """Check if a path from the sheet exists on disk (for UI badges)."""
    try:
        p = _resolve_under_root(path)
        return {"exists": True, "path": str(p)}
    except HTTPException as e:
        if e.status_code == 404:
            return {"exists": False, "path": path}
        raise
