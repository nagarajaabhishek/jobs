# Job Automation Pipeline

An automated system for sourcing, filtering, and evaluating job postings using **`LLMRouter`**: default **OpenRouter** (configurable model slugs) with optional **Gemini** / **OpenAI** providers for rollback.

## Master Architecture
```mermaid
graph TD
    subgraph Sourcing ["1. Sourcing Layer (High-Throughput)"]
        A[Sourcing Agent] --> B[JobSpy: LinkedIn/Indeed/Google]
        A --> C[Custom Scrapers: ATS/GH/Lever/Remotive]
        B & C --> D{AI Pre-filter & Tagging}
        D -- "Pass (Sniffed)" --> E[Google Sheets Client]
        D -- Reject --> F[Discard]
    end

    subgraph Intelligence ["2. Context & Strategic Nudges"]
        H[80/20 Location Prioritization] --> E
        I[Sponsorship Verification Loop] --> J
        K[Master Context & PDF Role Specs] --> G
        L[JD Cache: Local JSON Store] --> G
    end

    subgraph Logic ["3. Evaluation Layer (LLM)"]
        G[Evaluation Agent] --> M[LLM Router]
        M -- Primary --> N[OpenRouter / Gemini / OpenAI]
        N --> Q[Match Scoring 2.0 Rubric]
        J[Sponsorship Agent] --> G
    end

    subgraph Data ["4. Storage & Harvesting"]
        E --> R[(Google Sheet)]
        Q -- SSOT Verdict --> E
        Q -- Harvesting --> S[Skill Gaps / Tech Stacks / Salaries]
    end

    style M fill:#f9f,stroke:#333,stroke-width:2px
    style D fill:#bbf,stroke:#333,stroke-width:2px
```

## Features
- **Target-Driven Interleaved Pipeline**: Restructured to source and evaluate in 10/10 batches, providing immediate results and exiting once 50 "Must Apply" matches are found.
- **Dual-Model Strategy** (see `evaluation.*` in `config/pipeline.yaml`):
    - **Sourcing/Sniffing**: `sourcing_model` (OpenRouter slug when `provider: openrouter`).
    - **Deep Matching**: `openrouter_model` / `gemini_model` / `openai_model` depending on provider.

- **AI-Enhanced Sourcing**: 
    - **Smart Sniffing**: Drops irrelevant roles before they hit the sheet.
    - **Query Expansion**: Brainstorms search terms for better coverage.
- **Cloud-Powered Performance**: Deep evaluation with robust 429 rate limit resilience.

- **Full-cycle learning (optional)**:
    - **Post-LLM calibration**: Learned patterns in `data/learned_patterns.yaml` adjust scores (bounded), with `Calibration Delta`, `Base LLM Score`, and `Decision Audit JSON` on the sheet.
    - **Feedback**: Set `Feedback` / `Feedback Note` on rows, then run `apps/cli/scripts/tools/ingest_feedback.py` to merge into learned patterns (or enable `cycle.run_feedback_ingest` in `config/pipeline.yaml`).
    - **Daily digest**: After a run, digest files are written under `data/digests/` (see `digest.*` in `config/pipeline.yaml`). `cycle.run_digest_after_pipeline` runs digest generation and can mark `Digest Status` / `Action Link` on the sheet.

- **Automation guardrails**: `cycle.automation_hooks_enabled` is reserved for future hooks; it does **not** auto-apply to jobs—manual approval remains required.

- **Manual JD Tailor workflow (sheet-first)**:
    - Paste URLs into `Manual_JD_Tailor` and optionally set `Recommended Resume`.
    - Run one command (`--from-tailor-tab`) to fetch JD, tailor, run QA, generate `.tex/.pdf`, and write run status back to the sheet.
    - Output file naming now uses readable structured names (e.g., `AN_BA_<Position>_<Company>_Resume.pdf`) under `Resume_Building/Tailored/<Profile>/<JD_STEM>/`.
    - Optional post-tailor variant validation compares tailored vs generic-recommended YAML and writes winner columns to the sheet.

## Project Structure
- `apps/cli/run_pipeline.py`: Main daily pipeline entrypoint.
- `apps/cli/legacy/agents/`: Evaluation and legacy orchestration agents.
- `apps/cli/legacy/core/`: Shared clients (`GoogleSheetsClient`, `LLMRouter`, config, filters).
- `apps/cli/legacy/scrapers/`: Individual job site scrapers.
- `apps/cli/legacy/prompts/`: LLM system prompts.
- `apps/cli/scripts/`: Utility scripts categorized into `diagnostics/`, `tools/`, and `legacy/`.
- `config/`: Credentials, `pipeline.yaml`, and local JD cache.
- `data/`: Profiles, Master Context, and harvested insights.
- `apps/api/`: FastAPI backend for the ops dashboard ([apps/api/README.md](apps/api/README.md)); reads Google Sheets like the CLI.
- `apps/ops_dashboard/`: **Single-user ops UI** — jobs to apply, scores, resume links, tailored files ([apps/ops_dashboard/README.md](apps/ops_dashboard/README.md)).

## Architecture docs
- [docs/LAYERS_AND_PHASES.md](docs/LAYERS_AND_PHASES.md) — layer stack, build phases, SSOT trio with [CYCLE_SSOT](docs/CYCLE_SSOT.md) and [PRODUCT_CONTRACT](docs/PRODUCT_CONTRACT.md).
- [docs/CANONICAL_IMPORTS.md](docs/CANONICAL_IMPORTS.md) — production import paths (`apps/cli/legacy`, `core_agents`) vs legacy `src/`.
- [docs/CYCLE_HOOKS.md](docs/CYCLE_HOOKS.md) — post-run digest, feedback, filter learning, sourcing hints.
- [docs/TAILOR_QA_CHECKLIST.md](docs/TAILOR_QA_CHECKLIST.md) — tailoring QA and manual JD workflow.
- [docs/ROADMAP_THARA_ADVANCED.md](docs/ROADMAP_THARA_ADVANCED.md) — conversational/RAG/interview roadmap.

## Local deploy (website + optional API)

Mirrors the [Netlify](netlify.toml) build (`website_ui` → `dist`) and serves it with Vite preview, plus the FastAPI shell on port 8000.

```bash
cd /path/to/Job_Automation && chmod +x scripts/local_deploy.sh
./scripts/local_deploy.sh              # pip install, npm ci, build, then API + preview
./scripts/local_deploy.sh --dry-run    # install + build only (no servers)
SKIP_API=1 ./scripts/local_deploy.sh   # UI only (no `:8000`)
```

- **UI:** http://127.0.0.1:4173 (default) — same router as production (`/`, `/app`, `/architecture`, …).
- **API:** http://127.0.0.1:8000/docs when not using `SKIP_API=1`.

For HMR while editing React, use `cd website_ui && npm run dev` instead of this script, then open **http://localhost:5173/app** for the marketing **agent hub** shell.

### Ops dashboard (your pipeline: jobs, scores, resumes)

The product UI for **you** (no auth) lives in **`apps/ops_dashboard`**: Sheet-backed job list, detail with Evidence JSON, tailored file download.

```bash
# Terminal 1 — API (repo root)
PYTHONPATH=. uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — UI
cd apps/ops_dashboard && npm install && npm run dev
```

Open **http://127.0.0.1:5180**. See [apps/ops_dashboard/README.md](apps/ops_dashboard/README.md).

## Usage
Run the full pipeline from the repo root (so `config/pipeline.yaml` resolves):
```bash
cd /path/to/Job_Automation && python3 apps/cli/run_pipeline.py
```
For detailed agent instructions, see [.agent/workflows/job_pipeline.md](.agent/workflows/job_pipeline.md).

### Manual JD tailoring (recommended daily command)
```bash
cd /path/to/Job_Automation && python3 scripts/tools/tailor_from_urls.py --from-tailor-tab
```

This command now auto-handles:
- ensuring `Manual_JD_Tailor` exists (and required columns are present)
- reading URL + `Recommended Resume`
- tailoring + QA loop + LaTeX/PDF generation
- sheet updates per row: `Status`, `Last processed`, `Error`, validation scores, and **`Resume (PDF)` last** (absolute path to PDF or `.tex` fallback)
- variant comparison writeback: `Validation Verdict`, `Validation Reason`, `Tailored Score`, `Generic Score`, `Use Resume`

Disable variant comparison when needed:
```bash
cd /path/to/Job_Automation && python3 scripts/tools/tailor_from_urls.py --from-tailor-tab --no-validate-variants
```

Generate YAML only (skip QA/PDF):
```bash
cd /path/to/Job_Automation && python3 scripts/tools/tailor_from_urls.py --from-tailor-tab --skip-tailor-validation
```

Backfill validation scores for rows tailored before the sheet columns existed:
```bash
cd /path/to/Job_Automation && python3 scripts/tools/backfill_manual_tailor_validation.py --from-tailor-tab
```

## Configuration
- **Environment**: Copy `.env.example` to `.env`. Required LLM key depends on `evaluation.provider`: **`OPENROUTER_API_KEY`** (openrouter), **`GEMINI_API_KEY`** (gemini), or **`OPENAI_API_KEY`** (openai).
- **Google Sheet URL**: To use an existing workbook (recommended; avoids creating a new file in Drive), set either:
  - `sheet.spreadsheet_id` in `config/pipeline.yaml` (full URL or raw ID), or
  - `GOOGLE_SHEET_ID` in `.env` (same value).
  Precedence: constructor argument → `GOOGLE_SHEET_ID` / `GOOGLE_SHEETS_SPREADSHEET_ID` → `pipeline.yaml`. Share the sheet with the service account from `config/credentials.json` as **Editor**.
- **User profile context (required)**: Evaluation is grounded in your `master_context.yaml` and will fail fast if the compiled profile is missing or stale.
  - Ensure `data/profiles/master_context.yaml` exists.
  - Build/update the compiled context:

```bash
cd /path/to/Job_Automation && python3 apps/cli/scripts/tools/build_dense_matrix.py
```
- **Pipeline**: Edit `config/pipeline.yaml` to change:
    - `sourcing`: Queries, `expand_ai_queries`, `use_ai_filter`, `jobspy_sites`, and once-per-cycle endpoint toggles (`run_smartrecruiters_once`, `run_recruitee_once`) with company slug lists.
    - `sourcing.use_ai_filter`: When `true`, runs an extra LLM “sniffer” after static filters (more cost; use when scrapers return noisy titles). Default is `false` for higher sheet yield.
    - `sourcing.jobspy_sites`: Sites passed to JobSpy (default omits Glassdoor because it often errors on location).
    - `sourcing.smartrecruiters_companies` / `sourcing.recruitee_companies`: curated company slugs for optional public ATS pulls in the final community phase.
    - `filters`: Static rules (`inclusions`, `seniority_exclusions`, `seniority_soft_exclusions` + `seniority_soft_bypass_substrings`, locations). Each sourcing batch logs a **Sourcing filter summary** with reject counts by reason.
    - `evaluation`: `provider` (gemini), `gemini_model`.
    - `learning`: Enable/disable calibration, `max_abs_delta`, `patterns_path`.
    - `digest`: `top_n`, `output_dir`.
    - `cycle`: `run_digest_after_pipeline`, `run_feedback_ingest`, `automation_hooks_enabled`.

### Manual tools
```bash
# Merge sheet Feedback into data/learned_patterns.yaml and append data/feedback_events.jsonl
cd /path/to/Job_Automation && python3 apps/cli/scripts/tools/ingest_feedback.py

# Build today's digest (JSON + Markdown); optionally update sheet columns
cd /path/to/Job_Automation && python3 apps/cli/scripts/tools/build_job_digest.py --update-sheet

# Build career strategy (roles + sectors + upskilling) from recent evaluation signals
cd /path/to/Job_Automation && python3 apps/cli/scripts/tools/build_career_strategy.py
```

For a consolidated command + flags reference, see `docs/AGENT_COMMANDS.md`.

## Job descriptions (JD)
- **Local cache**: Full JDs are stored in `config/jd_cache.json` (keyed by canonical URL) to avoid cluttering Google Sheets while keeping evaluation context high.
- **Selector-only verification**: Evaluation only runs when the JD was extracted from known JD containers/selectors (e.g. `.job-description`, `#job-description`). Rows with `Status=NO_JD` are not evaluated.
- **Evidence-first decisions**: For evaluated rows, `Evidence JSON` contains the score breakdown and JD/profile evidence so you can audit why a verdict was given.

## Product contract & SSOT
- **Product Contract**: See `docs/PRODUCT_CONTRACT.md` for mission, purpose, and hard boundaries (no fabrication, no eval without verified JD/profile, auditability).
- **Cycle SSOT**: See `docs/CYCLE_SSOT.md` for the living Mermaid flow and preflight checklist. Regenerate it after architecture changes with:

```bash
cd /path/to/Job_Automation && python3 apps/cli/scripts/tools/generate_cycle_ssot.py
```

## Sorting & Verdicts
- **SSOT**: Sorting logic is centralized around a 0-100 "Apply Conviction Score". High scores (🔥/✅) are sorted to the top automatically.
