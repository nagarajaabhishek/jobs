---
description: How to run the job sourcing and evaluation pipeline
---

# Job Pipeline Workflow
// turbo-all

Follow these steps to perform a complete job sourcing and evaluation run for today.

1. **Prerequisites**
   - Ensure `.env` contains the necessary LLM key for `evaluation.provider` in `config/pipeline.yaml` (e.g. `OPENROUTER_API_KEY`, or `GEMINI_API_KEY` / `OPENAI_API_KEY` if using those providers).
   - Ensure `config/credentials.json` is present for Google Sheets.
   - Ensure the user profile context is compiled:
     - `data/profiles/master_context.yaml` exists (source of truth)
     - `data/dense_master_matrix.json` exists and is up-to-date (compiled context)
     - Build/update it with:
     ```bash
     cd /Users/abhisheknagaraja/Documents/Job_Automation && python3 apps/cli/scripts/tools/build_dense_matrix.py
     ```
   - If your profile lives elsewhere (development setup), set `PROFILE_DIR` (and optionally `MASTER_PROFILE_PATH`) in `.env` to point at your profile folder, then rebuild the dense matrix.
   - If `title_fit.enabled` is `true` in `config/pipeline.yaml`, ensure `title_fit_user.yaml` exists (see step 10 below) and `active_tracks` match files under `config/title_fit/tracks/` — otherwise preflight aborts before sourcing.

2. **Run Sourcing & Evaluation**
   // turbo
   Execute the central pipeline script (from repo root is best so `config/` paths resolve):
   ```bash
   cd /Users/abhisheknagaraja/Documents/Job_Automation && python3 apps/cli/run_pipeline.py
   ```
   Optional: set `sourcing.use_ai_filter: true` in `config/pipeline.yaml` only if you need LLM sniffing after static filters (extra API cost).
   Optional: enable additional once-per-cycle public ATS pulls with `sourcing.run_smartrecruiters_once` / `sourcing.run_recruitee_once` plus curated `smartrecruiters_companies` / `recruitee_companies` lists. Start with 3-5 slugs per source.

3. **Verify Results**
   - Check the Google Sheet "Resume_Agent_Jobs" under today's date tab.
   - Confirm jobs are marked as "EVALUATED".
   - Confirm "Match Type" and "Recommended Resume" are populated.

4. **Refine Results (Optional)**
   - If results are too broad, adjust `queries` in `config/pipeline.yaml` or filters in `apps/cli/legacy/core/job_filters.py`.

5. **Learning & digest (optional)**
   - After evaluation, the pipeline may run **cycle hooks** (see `cycle.*` in `config/pipeline.yaml`): digest generation writes `data/digests/<date>_digest.json` and `.md`; if `run_digest_after_pipeline` is true, top rows can be marked with `Digest Status` / `Action Link`.
   - To **train preferences**, set `Feedback` (e.g. `thumbs_up` / `thumbs_down`) and optional `Feedback Note` on sheet rows, then run `python3 apps/cli/scripts/tools/ingest_feedback.py`, or set `cycle.run_feedback_ingest: true` to run ingestion after the pipeline.
   - To **reduce wasted eval tokens from bad titles**, after you have many **EVALUATED** rows across dated tabs, run `python3 apps/cli/scripts/tools/learn_sourcing_filters_from_sheet.py` (optional `--dry-run`). It mines title phrases over-represented in low scores vs high scores into `data/sourcing_learned_title_blocks.yaml`. **Review and delete false positives**, then set `sourcing.apply_learned_title_blocks: true` in `config/pipeline.yaml`. This is interpretable pattern mining, not a separate ML model; it complements `title_fit` rules and post-eval `learned_patterns.yaml` calibration.
   - **Automation**: `cycle.automation_hooks_enabled` does not perform auto-apply; keep application decisions manual unless you add an approved workflow.
   - **Career strategy (optional)**: set `cycle.run_career_strategy: true` to write `data/strategy/career_strategy_<date>.{md,json}` after the cycle.

6. **Verify calibration columns**
   - For evaluated rows, confirm `Base LLM Score`, `Calibration Delta`, and `Decision Audit JSON` when `learning.enabled` is true.
   - For evaluated rows, confirm `Evidence JSON` is populated (score breakdown + JD quotes + profile evidence).

7. **SSOT docs (optional, recommended)**
   - Product boundaries: `docs/PRODUCT_CONTRACT.md`
   - Living cycle flow: `docs/CYCLE_SSOT.md` (regen via `python3 apps/cli/scripts/tools/generate_cycle_ssot.py`)

8. **Career-ops–inspired integrations (optional)**
   - **Story bank**: Edit `data/interview_story_bank.md` (STAR + reflection). A truncated excerpt is injected into the primary job-fit prompt so `Reasoning` stays aligned with how you tell behavioral stories.
   - **Negotiation / outreach copy**: Templates under `data/career_ops_templates/` (placeholders only; no auto-send).
   - **Portal seeds**: `config/portal_seeds.yml` merges extra Greenhouse/Lever/Ashby slugs into `sourcing.ats_boards` at runtime (see `apps/cli/legacy/core/config.py`).
   - **Deep packet (second LLM pass)**: In `config/pipeline.yaml`, set `evaluation.deep_eval_enabled: true` and optionally `deep_eval_min_score` (default 90). Writes `data/deep_packets/<date>_r<row>.md` and sets sheet column **Deep Packet** to the repo-relative path (or an `ERROR:` status). Uses `LLMRouter` (same `evaluation.provider` and fallbacks as the main eval; avoid large cloud batches without approval).
   - **Tailor JSON export**: Set `evaluation.export_tailor_json: true` to write `data/tailor_payloads/<date>_row<n>.json` for rows with final score ≥ 90. Or backfill from the sheet without re-eval: `python3 scripts/tools/export_tailor_payloads_from_sheet.py --min-score 90`.
   - **Sheet → TSV** (external TUI): `python3 scripts/tools/export_sheet_for_career_ops_tui.py` → `data/exports/sheet_export_<tab>.tsv` for a separate [career-ops](https://github.com/santifer/career-ops) dashboard clone.
   - **Integrity (read-only / maintenance)**: `python3 scripts/diagnostics/dedup_sheet_urls.py` (duplicate Job Links); `python3 scripts/diagnostics/normalize_sheet_statuses.py` (dry-run; add `--apply` to write).
   - **Licensing / ToS**: career-ops is MIT; respect third-party job-board and ATS terms when scraping or automating browsers.

9. **Parallel evaluation workers**
   - Multiple processes may run `evaluate_all` only if they target **disjoint row sets** (e.g. different tabs or pre-split row ranges). The same tab has no row locking; concurrent writers can overwrite each other.
   - Keep **periodic sheet sync every 2–5 evaluated jobs** (already implemented in `JobEvaluator`) so long runs stay visible in Google Sheets.

10. **Title and seniority fit (multi-track, multi-user)**
   - **Purpose**: Drop wrong-level titles (e.g. senior/meta PM) before sheet save and before LLM evaluation, using shared **track** definitions and a per-user file.
   - **Track catalog**: `config/title_fit/tracks/*.yaml` (e.g. product_management, business_analysis, program_project_management). Edit or add tracks for new role families.
   - **User profile**: `data/profiles/title_fit_user.yaml` (or next to `MASTER_PROFILE_PATH` if set). Set `active_tracks`, `policy` (`conservative` / `balanced` / `aggressive`), `first_formal_role_flags`, optional `effective_yoe` (defaults from `dense_master_matrix.json`), and **`include_internship_entry_signals`** (`false` by default: internships are not mixed into FT job entry signals; set `true` when sourcing PM/BA/program internships).
   - **Pipeline**: In `config/pipeline.yaml`, set `title_fit.enabled: true` when ready. Defaults stay `false` so existing runs are unchanged.
   - **Preflight**: When `title_fit.enabled` is true, `run_cycle_preflight` in `apps/cli/legacy/core/preflight.py` (called from `apps/cli/run_pipeline.py` before sourcing) **fails fast** if `title_fit_user.yaml` is missing, `active_tracks` is empty, any track id is unknown, there are no track YAMLs under `config/title_fit/tracks/`, or LLM disambiguation is on without the required API key (`OPENROUTER_API_KEY`, `GEMINI_API_KEY`, or `OPENAI_API_KEY` per `evaluation.provider`).
   - **Behavior**: `apps/cli/legacy/core/title_fit_gate.py` runs from `passes_sourcing_filter` and `passes_evaluation_prefilter` in `job_filters.py`. Reject reasons appear in sourcing stats as `Title fit: ...`.
   - **Optional LLM**: `title_fit.llm_disambiguation_enabled: true` disambiguates titles that match **ambiguous** tokens (uses `LLMRouter` / `disambiguation_model` or sourcing model). **Conservative** policy rejects ambiguous titles when LLM is off.
   - **AI sniffer**: When `sourcing.use_ai_filter` is on, `ai_sniff_relevance` builds role text from `active_tracks` display names and `title_fit_user.yaml` constraints instead of a hardcoded PM-only list.
   - **Tests**: `pytest tests/test_title_fit_gate.py tests/test_preflight_title_fit.py`
   - **Multi-user v1**: One active profile per run via `PROFILE_DIR` / `MASTER_PROFILE_PATH`; optional per-row `Owner` column can be added later without changing the gate API.
