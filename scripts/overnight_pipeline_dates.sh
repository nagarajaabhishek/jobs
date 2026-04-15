#!/usr/bin/env bash
#
# Run apps/cli/run_pipeline.py once per sheet tab date, from START_DATE down to END_DATE (inclusive).
# Logs all output to OVERNIGHT_LOG (default: repo logs/overnight_pipeline_<timestamp>.log).
#
# Usage (from repo root):
#   chmod +x scripts/overnight_pipeline_dates.sh
#   START_DATE=2026-04-09 END_DATE=2026-04-01 ./scripts/overnight_pipeline_dates.sh
#
# Optional env:
#   ROOT              — repo root (default: parent of this script)
#   SLEEP_AFTER_OK_SEC   — seconds after a successful run (default: 90)
#   SLEEP_AFTER_FAIL_SEC — seconds after a failed run (default: 180)
#   PIPELINE_DATE_RETRIES — max attempts per date (default: 1)
#   OVERNIGHT_LOG     — log file path
# macOS: keep the machine awake while this runs, wrap the invocation:
#   caffeinate -dimsu env START_DATE=... END_DATE=... ./scripts/overnight_pipeline_dates.sh
#
set -euo pipefail

ROOT="${ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
START_DATE="${START_DATE:?Set START_DATE=YYYY-MM-DD}"
END_DATE="${END_DATE:?Set END_DATE=YYYY-MM-DD}"
SLEEP_OK="${SLEEP_AFTER_OK_SEC:-90}"
SLEEP_FAIL="${SLEEP_AFTER_FAIL_SEC:-180}"
RETRIES="${PIPELINE_DATE_RETRIES:-1}"
LOG="${OVERNIGHT_LOG:-$ROOT/logs/overnight_pipeline_$(date +%Y-%m-%d_%H%M%S).log}"
mkdir -p "$(dirname "$LOG")"

prev_date() {
  if [[ "$(uname -s)" == "Darwin" ]]; then
    date -j -v-1d -f "%Y-%m-%d" "$1" "+%Y-%m-%d"
  else
    date -d "$1 -1 day" "+%Y-%m-%d" 2>/dev/null || date --date "$1 -1 day" "+%Y-%m-%d"
  fi
}

run_one_date() {
  local d="$1"
  local attempt=1
  while [[ "$attempt" -le "$RETRIES" ]]; do
    echo "===== $(date '+%Y-%m-%d %H:%M:%S %Z') Running SHEET_TAB_DATE=$d (attempt $attempt/$RETRIES) =====" | tee -a "$LOG"
    set +e
    ( cd "$ROOT" && SHEET_TAB_DATE="$d" python3 apps/cli/run_pipeline.py ) 2>&1 | tee -a "$LOG"
    local rc=${PIPESTATUS[0]}
    set -e
    if [[ "$rc" -eq 0 ]]; then
      echo "===== OK $d =====" | tee -a "$LOG"
      return 0
    fi
    echo "===== FAILED $d exit=$rc =====" | tee -a "$LOG"
    attempt=$((attempt + 1))
    if [[ "$attempt" -le "$RETRIES" ]]; then
      echo "Retrying $d after ${SLEEP_FAIL}s..." | tee -a "$LOG"
      sleep "$SLEEP_FAIL"
    fi
  done
  return 1
}

inner_loop() {
  local d="$START_DATE"
  while [[ "$d" > "$END_DATE" || "$d" == "$END_DATE" ]]; do
    if run_one_date "$d"; then
      sleep "$SLEEP_OK"
    else
      sleep "$SLEEP_FAIL"
    fi
    [[ "$d" == "$END_DATE" ]] && break
    d="$(prev_date "$d")"
  done
  echo "All scheduled dates complete ($START_DATE -> $END_DATE). Log: $LOG"
}

inner_loop
