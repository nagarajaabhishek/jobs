---
description: How to debug job sourcing yield and bias (JobSpy vs Jobright).
---

# SOP: Sourcing & Yield Debugging

Use this procedure when the sourcing step returns 0 results, 100% of jobs are from a single source, or relevant jobs are being missed.

### 1. Check Job Distribution
Analyze the current "Source" distribution in the Google Sheet.
// turbo
```bash
python3 scripts/diagnostics/check_sources.py
```

### 2. Deep Filter Debug
Run a live trace on JobSpy to see exactly which condition (Title, Location, Seniority) is rejecting jobs.
// turbo
```bash
python3 scripts/diagnostics/debug_filters_deep.py
```

### 3. Verify Jobright Connectivity
If Jobright results are missing, test the specialized scraper directly.
// turbo
```bash
python3 scripts/diagnostics/debug_jobspy.py
```

### Common Fixes
- **Location Mismatch**: Update `ALLOWED_LOCATIONS` in `src/core/job_filters.py` if a city name is being rejected.
- **Over-filtering**: If "Seniority Exclusion" is too aggressive, adjust the `SENIOR_KEYWORDS` list.
- **Source Bias**: Ensure `run_pipeline.py` prioritizes direct sources (JobSpy) before aggregators (Jobright).
