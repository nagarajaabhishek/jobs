# Scripts Directory

This directory contains utility scripts for the Job Automation Pipeline, organized by their purpose.

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
