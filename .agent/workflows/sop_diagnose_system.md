---
description: How to diagnose the local environment, Ollama, and LLM connectivity.
---

# SOP: System Diagnostics & LLM Health

This SOP outlines the steps to verify that the local environment, Ollama instance, and LLM models are healthy and correctly configured for the job automation pipeline.

### Prerequisites
- Ollama must be installed and running on the host machine.
- Environment variables (if any) should be configured in `.env`.

### 1. Verify Ollama Connection
Run the primary diagnostic script to check if the Ollama API is reachable.
// turbo
```bash
python3 scripts/diagnostics/diagnose_ollama.py
```

### 2. Test Model Response & Parsing
Verify that the specific model (e.g., `qwen2.5:7b`) is responsive and its output is matchable by our regex filters.
// turbo
```bash
python3 scripts/diagnostics/verify_ollama_fallback.py
```

### 3. Check Overall Sourcing Filter Reliability
Ensure the static filters aren't over-filtering or under-filtering jobs.
// turbo
```bash
python3 scripts/diagnostics/verify_filters.py
```

### Troubleshooting
- **Ollama 404/Connection Error**: Ensure the Ollama app is running in the background. Run `ollama list` in a terminal to confirm.
- **Parsing Errors**: If evaluations fail to parse, update the regex in `src/agents/evaluate_jobs.py` to match the model's new response style.
