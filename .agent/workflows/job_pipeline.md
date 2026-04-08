---
description: How to run the job sourcing and evaluation pipeline
---

# Job Pipeline Workflow
// turbo-all

Follow these steps to perform a complete job sourcing and evaluation run for today.

1. **Prerequisites**
   - Ensure `.env` contains the necessary configuration (e.g., `GEMINI_API_KEY`).
   - Ensure `config/credentials.json` is present for Google Sheets.
   - Ensure the user profile context is compiled:
     - `data/profiles/master_context.yaml` exists (source of truth)
     - `data/dense_master_matrix.json` exists and is up-to-date (compiled context)
     - Build/update it with:
     ```bash
     cd /Users/abhisheknagaraja/Documents/Job_Automation && python3 apps/cli/scripts/tools/build_dense_matrix.py
     ```
   - If your profile lives elsewhere (development setup), set `PROFILE_DIR` (and optionally `MASTER_PROFILE_PATH`) in `.env` to point at your profile folder, then rebuild the dense matrix.

2. **Run Sourcing & Evaluation**
   // turbo
   Execute the central pipeline script (from repo root is best so `config/` paths resolve):
   ```bash
   cd /Users/abhisheknagaraja/Documents/Job_Automation && python3 apps/cli/run_pipeline.py
   ```
   Optional: set `sourcing.use_ai_filter: true` in `config/pipeline.yaml` only if you need LLM sniffing after static filters (extra API cost).

3. **Verify Results**
   - Check the Google Sheet "Resume_Agent_Jobs" under today's date tab.
   - Confirm jobs are marked as "EVALUATED".
   - Confirm "Match Type" and "Recommended Resume" are populated.

4. **Refine Results (Optional)**
   - If results are too broad, adjust `queries` in `config/pipeline.yaml` or filters in `apps/cli/legacy/core/job_filters.py`.

5. **Learning & digest (optional)**
   - After evaluation, the pipeline may run **cycle hooks** (see `cycle.*` in `config/pipeline.yaml`): digest generation writes `data/digests/<date>_digest.json` and `.md`; if `run_digest_after_pipeline` is true, top rows can be marked with `Digest Status` / `Action Link`.
   - To **train preferences**, set `Feedback` (e.g. `thumbs_up` / `thumbs_down`) and optional `Feedback Note` on sheet rows, then run `python3 apps/cli/scripts/tools/ingest_feedback.py`, or set `cycle.run_feedback_ingest: true` to run ingestion after the pipeline.
   - **Automation**: `cycle.automation_hooks_enabled` does not perform auto-apply; keep application decisions manual unless you add an approved workflow.
   - **Career strategy (optional)**: set `cycle.run_career_strategy: true` to write `data/strategy/career_strategy_<date>.{md,json}` after the cycle.

6. **Verify calibration columns**
   - For evaluated rows, confirm `Base LLM Score`, `Calibration Delta`, and `Decision Audit JSON` when `learning.enabled` is true.
   - For evaluated rows, confirm `Evidence JSON` is populated (score breakdown + JD quotes + profile evidence).

7. **SSOT docs (optional, recommended)**
   - Product boundaries: `docs/PRODUCT_CONTRACT.md`
   - Living cycle flow: `docs/CYCLE_SSOT.md` (regen via `python3 apps/cli/scripts/tools/generate_cycle_ssot.py`)
