# Sponsorship and H-1B signaling

## Production path (canonical)

The daily pipeline evaluates jobs with **`JobEvaluator`** ([`apps/cli/legacy/agents/evaluate_jobs.py`](../apps/cli/legacy/agents/evaluate_jobs.py)). The model outputs H-1B / sponsorship-related fields as part of structured evaluation, which are written to Google Sheet columns (e.g. the `H1B Sponsorship` pillar per project rules).

This path runs **only** for rows with verified JD text and user context per [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md).

## Standalone `SponsorshipAgent`

[`src/agents/sponsorship_agent.py`](../src/agents/sponsorship_agent.py) defines a small **batch** helper that reads evaluated rows and runs a one-word YES/NO/UNKNOWN style prompt. It is **not** wired into [`apps/cli/run_pipeline.py`](../apps/cli/run_pipeline.py).

Use it only for explicit one-off diagnostics or if you deliberately script sponsorship passes separate from fit evaluation.

## Naming

References to a “Sponsorship Agent” in architecture diagrams may mean either:

1. The **evaluator-integrated** sponsorship analysis (primary), or  
2. The **standalone** `SponsorshipAgent` class (secondary, `src/` only).

When updating docs or diagrams, prefer naming **“sponsorship fields from JobEvaluator”** for the production path to avoid confusion.
