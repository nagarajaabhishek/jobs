# Canonical import paths

## Production pipeline (use these for new code)

| Concern | Location |
|---------|----------|
| Main entry | `apps/cli/run_pipeline.py` |
| Job evaluation + sheet batching | `apps.cli.legacy.agents.evaluate_jobs` (`JobEvaluator`) |
| Sourcing | `core_agents.sourcing_agent.agent` (`SourcingAgent`) |
| Resume tailoring | `core_agents.resume_agent.tailor` (`TailorAgent`) |
| Config | `apps.cli.legacy.core.config` |
| Google Sheets | `apps.cli.legacy.core.google_sheets_client` |
| LLM routing | `apps.cli.legacy.core.llm_router` |
| Preflight | `apps.cli.legacy.core.preflight` |

## Legacy `src/` tree

The `src/` package duplicates older paths (`src.agents.evaluate_jobs`, `src.core.google_sheets_client`, …) used by some tests and ad-hoc scripts under `scripts/`. **Do not add new features to `src/`** unless you are maintaining those call sites.

**Sponsorship:** H-1B / sponsorship signals for evaluated rows are produced by **`JobEvaluator`** (prompt + structured columns). The standalone `src/agents/sponsorship_agent.py` (`SponsorshipAgent`) is a separate batch utility and is **not** invoked by `run_pipeline.py`. See [SPONSORSHIP.md](SPONSORSHIP.md).

## Consolidation guideline

When touching evaluation or sheets logic, implement in **`apps/cli/legacy/`** and update tests to import from there over time. This avoids two divergent `JobEvaluator` implementations.
