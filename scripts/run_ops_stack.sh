#!/usr/bin/env bash
# Start FastAPI (8000) and ops dashboard dev server (5180). Repo root = Job_Automation.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"
python3 -m uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000 &
PID=$!
trap 'kill "$PID" 2>/dev/null || true' EXIT INT TERM
cd "$ROOT/apps/ops_dashboard"
exec npm run dev
