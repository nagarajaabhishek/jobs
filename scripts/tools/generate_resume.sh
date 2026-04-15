#!/usr/bin/env bash
# Run the resume agent generator from repo root. The script expects CWD to be
# core_agents/resume_agent (templates and meta paths are relative to that tree).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT/core_agents/resume_agent"
exec python3 .agent/scripts/generate_resume.py "$@"
