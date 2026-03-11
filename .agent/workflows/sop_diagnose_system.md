---
description: How to diagnose the local environment and Gemini API connectivity.
---

# SOP: System Diagnostics & LLM Health

This SOP outlines the steps to verify that the local environment and Gemini/OpenRouter APIs are healthy and correctly configured for the job automation pipeline.

### Prerequisites
- Environment variables (`OPENROUTER_API_KEY`, `GEMINI_API_KEY`) should be configured in `.env`.

### 1. Verify Gemini API Connection
Run the diagnostic script to check if the Gemini API is reachable and quota is active.
// turbo
```bash
python3 scripts/diagnostics/test_gemini_quota_v4.py
```

### 2. Test Model Response & Parsing
Verify that the model is responsive and its output is matchable by our regex filters.
// turbo
```bash
python3 scripts/diagnostics/test_raw_eval.py
```

### 3. Check Overall Sourcing Filter Reliability
Ensure the static filters aren't over-filtering or under-filtering jobs.
// turbo
```bash
python3 scripts/diagnostics/verify_filters.py
```

### Troubleshooting
- **API Connection Error**: Ensure your `.env` contains valid API keys with available credits.
- **Parsing Errors**: If evaluations fail to parse JSON properly, update `src/agents/evaluate_jobs.py` to handle the model's new response style.
