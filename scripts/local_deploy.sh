#!/usr/bin/env bash
# Local "deploy": production build of the marketing/app shell + optional API (mirrors Netlify build).
# Usage:
#   ./scripts/local_deploy.sh           # install deps, build UI, start API + Vite preview
#   ./scripts/local_deploy.sh --dry-run # install + build only
# Env:
#   SKIP_API=1           — only serve website_ui (no FastAPI on :8000)
#   PREVIEW_PORT=4173    — Vite preview port (default 4173)
#   API_PORT=8000        — Uvicorn port (default 8000)

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

PREVIEW_PORT="${PREVIEW_PORT:-4173}"
API_PORT="${API_PORT:-8000}"

echo "==> Job_Automation local deploy (repo root: $ROOT)"

echo "==> Python dependencies"
python3 -m pip install -q -r requirements.txt

echo "==> website_ui: npm ci && npm run build"
cd "$ROOT/website_ui"
npm ci
npm run build

if [[ "$DRY_RUN" == 1 ]]; then
  echo "==> Dry run complete (skipping servers). Build output: website_ui/dist"
  exit 0
fi

cleanup() {
  if [[ -n "${API_PID:-}" ]] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

if [[ "${SKIP_API:-}" != "1" ]]; then
  echo "==> Starting API: http://127.0.0.1:${API_PORT} (docs: /docs, health: /health)"
  cd "$ROOT"
  PYTHONPATH="$ROOT" python3 -m uvicorn apps.api.main:app --host 127.0.0.1 --port "$API_PORT" &
  API_PID=$!
else
  echo "==> SKIP_API=1 — not starting FastAPI"
fi

echo "==> Starting Vite preview (Netlify-style static): http://127.0.0.1:${PREVIEW_PORT}"
echo "    Open /app for the dashboard shell. Ctrl+C stops all servers."
cd "$ROOT/website_ui"
npm run preview -- --host 127.0.0.1 --port "$PREVIEW_PORT"
