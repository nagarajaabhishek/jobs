# Cycle hooks (post-pipeline)

End-of-run behavior is controlled by `cycle.*` in [`config/pipeline.yaml`](../config/pipeline.yaml) and invoked from `_run_cycle_hooks()` in [`apps/cli/run_pipeline.py`](../apps/cli/run_pipeline.py).

## Flags and scripts

| Config key | Default (see YAML) | Script / effect |
|------------|-------------------|-----------------|
| `run_digest_after_pipeline` | `true` | `build_job_digest` — writes digest under `digest.output_dir`, optional sheet columns |
| `run_feedback_ingest` | `false` | `ingest_feedback` — merges sheet feedback into `data/learned_patterns.yaml` |
| `run_career_strategy` | `false` | `build_career_strategy` — strategy artifact under `data/strategy/` |
| `run_filter_learning` | `true` | `learn_sourcing_filters_from_sheet` — mines title phrases → `filter_learning_output` |
| `run_sourcing_hints` | `true` | `suggest_sourcing_sources` — ranked sources/companies → `sourcing_hints_output` |
| `automation_hooks_enabled` | `false` | Log-only; does not auto-apply (policy) |

## Validation checklist

1. **Digest:** After a successful pipeline, confirm `data/digests/` (or configured dir) has a new file and sheet `Digest Status` / links if enabled in digest tool.
2. **Feedback ingest:** Enable `run_feedback_ingest: true` only after populating `Feedback` / `Feedback Note` on rows; verify `data/learned_patterns.yaml` changes match expectations (bounded deltas per `learning.max_abs_delta`).
3. **Filter learning:** Review generated YAML before relying on `apply_learned_title_blocks` for aggressive filtering.
4. **Sourcing hints:** Inspect `data/sourcing_hints.yaml` for sensible top sources; no LLM cost.
5. **Career strategy:** First run with `run_career_strategy: true` in a dry environment; confirm output path and no sheet blast.

## Cost note

Only hooks that invoke LLMs (indirectly via shared tooling) matter for billing. Digest/career tools follow `evaluation`/router config where applicable. Keep `run_feedback_ingest` off until you intend to merge human labels.
