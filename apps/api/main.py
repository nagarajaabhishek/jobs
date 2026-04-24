"""
FastAPI layer for the Job Automation ops dashboard.

Run from repository root:
  PYTHONPATH=. uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000

Frontend: apps/ops_dashboard (Vite, proxies /api -> this server).
"""

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from apps.api.paths import PROJECT_ROOT
from apps.api.routers import files as files_router
from apps.api.routers import jobs as jobs_router

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
except ImportError:
    pass

app = FastAPI(
    title="Job Automation API",
    version="0.2.0",
    description="Ops dashboard backend: Google Sheets job rows + resume file serving.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5180",
        "http://localhost:5180",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router.router, prefix="/api/v1", tags=["jobs"])
app.include_router(files_router.router, prefix="/api/v1", tags=["files"])


def _require_api_key(x_api_key: Optional[str]) -> None:
    expected = (os.environ.get("JOB_AUTOMATION_API_KEY") or "").strip()
    if not expected:
        return
    if (x_api_key or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/meta")
def meta(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> Dict[str, Any]:
    _require_api_key(x_api_key)
    return {
        "pipeline_entrypoint": "apps/cli/run_pipeline.py",
        "ops_dashboard": "apps/ops_dashboard",
        "docs": "docs/LAYERS_AND_PHASES.md",
    }


# Legacy path kept for older clients
@app.get("/v1/jobs")
def list_jobs_legacy(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> Dict[str, Any]:
    _require_api_key(x_api_key)
    return {
        "items": [],
        "message": "Use GET /api/v1/jobs instead.",
    }
