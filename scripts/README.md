# Scripts Directory

This directory contains utility scripts for the Job Automation Pipeline, organized by their purpose.

## Root-level scripts

- **`local_deploy.sh`**: Local production-style deploy — `pip install`, `website_ui` `npm ci` + build, then optional FastAPI + Vite preview (see root [README.md](../README.md#local-deploy-website--optional-api)).
- **`run_ops_stack.sh`**: Start FastAPI on `:8000` and the **ops dashboard** dev server (`apps/ops_dashboard`, `:5180`). Requires two processes; use this for a one-command local stack.

## Subdirectories

### `diagnostics/`
Scripts for testing API connectivity, quotas, and model performance.
- `test_gemini_quota.py`: Basic quota check.
- `test_gemini_quota_v2.py`: Expanded quota and latency test.

### `tools/`
Verification tools and standalone utilities.
- `verify_sourcing_flow.py`: Standalone script to test scraping and filtering.

### `legacy/`
Older scripts or one-off data fetching/analysis tasks.
- `analyze_0223_data.py`: Specific analysis for Feb 23rd batch.
- `fetch_0223_data.py`: Data retrieval for Feb 23rd batch.
