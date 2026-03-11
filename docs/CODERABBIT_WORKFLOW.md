# CodeRabbit Workflow: Job_Automation

This document explains how CodeRabbit helps maintain the quality and security of the `Job_Automation` pipeline.

## Automated Review Lifecycle

1.  **PR Initialization**: CodeRabbit automatically triggers on every pull request to `main`, `master`, or `develop`.
2.  **Scraper Audit**: It specifically checks `sourcing_agent.py` and new scraper modules for:
    - Robustness (retries/error handling).
    - Compliance with the "Missing JD" fallback protocol.
3.  **Prompt Safety**: It monitors `src/prompts/` to ensure changes to Gemini fit-analyst instructions don't break JSON structure.
4.  **Security Gate**: It scans for leaked API keys or Sheet credentials.

## Interacting with CodeRabbit

- **Manual Review**: Comment `@coderabbitai review` on any PR to force a re-audit.
- **Deep Dive**: Comment `@coderabbitai explain this logic` to get a technical breakdown of complex agent loops.
- **Summary**: CodeRabbit will automatically post a high-level summary of changes and their potential impact on the pipeline maturity.

## Best Practices

- **Check Score Consistency**: If you modify `evaluate_jobs.py`, ensure CodeRabbit confirms the 0-100 scoring contract is intact.
- **Scraper Compliance**: Always ensure scrapers return the canonical job object. CodeRabbit will flag inconsistencies.
