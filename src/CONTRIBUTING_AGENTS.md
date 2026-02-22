# Agent Contribution Guide

Welcome, fellow agent. This project is optimized for automated job sourcing and evaluation.

## Architecture Overview
- **Core (`src/core/`)**: Low-level clients for Google Sheets, Ollama (LLM), and Database.
- **Scrapers (`src/scrapers/`)**: Target-specific logic for fetching job data.
- **Agents (`src/agents/`)**: High-level orchestrators that filter and evaluate jobs.
- **Prompts (`src/prompts/`)**: Markdown-based system prompts for the LLMs.

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
