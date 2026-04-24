# Ops dashboard (Job Automation)

Single-user web UI for your pipeline data: jobs to apply, scores, resume variant, H1B column, tailored file links. **No authentication** (local / trusted network only).

## Prerequisite

Run the API from the **repository root** (same as CLI — needs `config/credentials.json`, `config/pipeline.yaml`, optional `.env`):

```bash
cd /path/to/Job_Automation
PYTHONPATH=. uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000
```

## Frontend

```bash
cd apps/ops_dashboard
npm install
npm run dev
```

Open **http://127.0.0.1:5180** (Vite proxies `/api` → `:8000`).

## What it uses

- `GET /api/v1/jobs` — rows on the daily Sheet tab (same tab logic as `get_worksheet_tab_date()`).
- `GET /api/v1/jobs/detail?url=` — full row including **Evidence JSON** and reasoning.
- `GET /api/v1/files/resume?path=` — serve PDF/TEX only if the path resolves under the repo root.

Optional: set `JOB_AUTOMATION_API_KEY` and send `X-API-Key` on requests (not wired in this UI yet).

## Production build

```bash
npm run build
npm run preview
```

Serve `dist/` behind your reverse proxy and point API requests at the same host or configure Vite `base` / env `VITE_API_URL` if you split origins later.
