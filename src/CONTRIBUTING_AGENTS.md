# Agent Contribution Guide

Welcome, fellow agent. This project is optimized for automated job sourcing and evaluation.

**Canonical production code** lives under `apps/cli/legacy/` and `core_agents/` (see [docs/CANONICAL_IMPORTS.md](../docs/CANONICAL_IMPORTS.md)). The `src/` tree remains for legacy tests and scripts; prefer extending the legacy paths for new pipeline features.

## Architecture Overview
- **Core (`src/core/`)**: Legacy low-level clients (many scripts still import here). Prefer `apps/cli/legacy/core/` for new work.
- **Scrapers (`src/scrapers/`)**: Legacy mirror; production scrapers are under `apps/cli/legacy/scrapers/`.
- **Agents (`src/agents/`)**: Legacy orchestrators; production `JobEvaluator` is `apps/cli/legacy/agents/evaluate_jobs.py`.
- **Prompts (`src/prompts/`)**: Markdown prompts; mirrored under `apps/cli/legacy/prompts/` for the CLI pipeline.

## Operational Flow
1. **Incremental Sourcing**: `sourcing_agent.py` saves to Google Sheets after *each* query loop. This prevents data loss if a scraper crashes.
2. **Transparent Filtering**: All skip decisions are logged via `logging.info`. If a job is missing, check the console/logs for `Skipped: [Reason]`.
3. **Single pipeline pass**: `run_pipeline.py` runs community sources once, JobSpy in parallel (all query × location), then one evaluation pass. Evaluation saves in batches of 25 to reduce API calls.
4. **Resilient Evaluation**: Batch updates protect progress; calibration summary and Maybe > 80% warning surface evaluation quality.


## How to Help
- **Adding a Scraper**: Create a new class in `src/scrapers/` and register it in `sourcing_agent.py`.
- **Refining Evaluation**: Modify `src/prompts/gemini_job_fit_analyst.md` or the parser in `evaluate_jobs.py`.

## Workflows
Use the structured workflows in `.agent/workflows/` for routine operations.
