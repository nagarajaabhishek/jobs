# Job Automation API

Backend for the **ops dashboard** ([`apps/ops_dashboard`](../ops_dashboard/README.md)). It reads the same **Google Sheet** as the CLI via `GoogleSheetsClient`. Running the pipeline still uses `apps/cli/run_pipeline.py`.

## Run locally (repo root)

```bash
cd /path/to/Job_Automation
pip install -r requirements.txt
PYTHONPATH=. uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` (OpenAPI) and `http://127.0.0.1:8000/health`.

## Auth (optional)

| Mechanism | Use |
|-----------|-----|
| **None** | Default: no `JOB_AUTOMATION_API_KEY` — suitable for local single-user dashboard. |
| **API key** | Set `JOB_AUTOMATION_API_KEY`; send `X-API-Key` on `/api/v1/meta` only if you enable it there. Job and file routes do not require the key unless extended. |

Bind to `127.0.0.1` on untrusted networks. Service-account JSON must never be exposed via HTTP.

## Primary endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/jobs` | List job rows (query: `tab`, `min_score`, `limit`, `must_apply_only`, `has_resume`) |
| GET | `/api/v1/jobs/detail?url=` | Full row (Evidence JSON, reasoning, resume path, …) |
| GET | `/api/v1/meta/sheet` | Resolved worksheet tab + spreadsheet id preview |
| GET | `/api/v1/files/resume?path=` | Serve file only under repository root (paths from `Resume Path`) |
| GET | `/api/v1/files/exists?path=` | Check file exists |

CORS allows the Vite dev server on port **5180** (see `main.py`).
