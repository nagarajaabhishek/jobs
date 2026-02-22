# Application Grade: Job Automation Pipeline

**Scope:** Evaluation of the application as originally developed (prior to the recent chat’s evals, calibration, and efficiency changes).  
**Purpose (from README):** *An automated system for sourcing, filtering, and evaluating job postings using local LLMs (Ollama) and Google Sheets.*

---

## Overall Grade: **B–** (Good fit for purpose, solid structure; several bugs and gaps)

---

## 1. Alignment with Purpose & Goals — **A–**

| Goal | Assessment |
|------|------------|
| **Sourcing** | ✅ Multiple sources (JobSpy, Community, Jobright, Arbeitnow, ATS). Clear separation of scrapers. |
| **Filtering** | ✅ Rule-based filter (title, location, seniority, exclusions) with logging. |
| **Evaluating** | ✅ LLM-based evaluation with structured output (Match Type, Recommended Resume, H1B, etc.). |
| **Google Sheets** | ✅ Daily tab, add jobs, dedupe by URL, batch updates, sort by match priority. |
| **Local LLM** | ✅ Ollama integrated; prompt + profile loaded from files. |

**Deductions:** Evaluation quality was under-specified (no evals or calibration), so “evaluating” was only partially validated. Sponsorship agent was broken (wrong imports, missing `self.llm`), so that part of the product did not run.

---

## 2. Architecture & Structure — **B+**

**Strengths:**
- Clear layering: `core/` (Sheets, LLM, DB), `scrapers/`, `agents/`, `prompts/`.
- Single entry point (`run_pipeline.py`) and documented workflow (`.agent/workflows/job_pipeline.md`).
- CONTRIBUTING_AGENTS.md explains flow and how to add scrapers.
- `LocalDatabase` exists and is documented as swappable with Sheets (though unused in the main pipeline).

**Weaknesses:**
- `LocalDatabase` is never used; pipeline is Sheets-only. Either use it or remove to avoid confusion.
- Sponsorship agent lives in `agents/` but is not wired into the main pipeline and was broken at the call site (`self.llm` undefined).
- No shared interface for “LLM that returns (text, engine)”—each consumer does its own thing (Ollama subprocess vs Gemini client).

---

## 3. Code Quality — **B**

**Strengths:**
- Readable naming and coherent file layout.
- Filter logic is explicit (inclusion/exclusion lists, logging of skips).
- Sheets client handles missing tab, creates headers, and batches updates.
- Evaluation parser uses regex for Markdown sections and fallbacks for robustness.

**Weaknesses:**
- **Bugs:** Sponsorship agent: wrong import path (`google_sheets_client`), `self.llm` never set. Parser regex for “Skill Gap Summary” missed leading `**`. Tests used top-level imports (`llm_router`, `evaluate_jobs`, `google_sheets_client`) and referenced `openai_client`, which doesn’t exist.
- **Hardcoding:** Profile path in evaluator is absolute and user-specific (`/Users/.../Resume_Agent/.agent/data/Abhishek/`). No config or env for paths.
- **Doc typo:** CONTRIBUTING says “parser in `evaluate_evals.py`” but the file is `evaluate_jobs.py`.
- **Minor:** `import re` inside a loop in `filter_jobs`; could be at module top.

---

## 4. Robustness & Resilience — **B**

**Strengths:**
- Incremental save: jobs written after each JobSpy batch to limit loss on failure.
- Evaluation writes in batches of 10 to reduce API usage and protect progress.
- Sheets: create spreadsheet/tab and headers if missing; `get_existing_urls` for dedupe across tabs.
- Try/except around scrapers and LLM with fallbacks (e.g. empty string / “FAILED”).

**Weaknesses:**
- No retries for transient failures (network, Sheets rate limits).
- `get_existing_urls()` ran on every `add_jobs()`, causing heavy repeated reads when adding many batches.
- One subprocess per evaluation (Ollama) added process overhead and no connection reuse.

---

## 5. Maintainability & Extensibility — **B+**

**Strengths:**
- Adding a scraper is straightforward: new class in `scrapers/`, register in sourcing agent.
- Prompts in Markdown; evaluation schema (Match Type, Recommended Resume, etc.) is consistent.
- Workflow registry + step logging give a clear run narrative.

**Weaknesses:**
- No evals or metrics to guard regressions when changing prompts or parser.
- Queries/locations and batch sizes are hardcoded in `run_pipeline.py` and evaluator; no config file or env.
- Scrapers return slightly different shapes (e.g. some with `description`, some without); normalizer papers over it but the contract is implicit.

---

## 6. Testing — **C+**

**Strengths:**
- Test files exist for sheet client, Ollama/evaluator, and models.
- Root-level `test_sheet.py` and `test_ollama_logic.py` give quick manual checks.

**Weaknesses:**
- Tests used incorrect imports (no `src.`), so they failed when run from project root.
- test_ollama referenced `evaluator.llm.openai_client`, which doesn’t exist in the Ollama-only design.
- No automated tests for filter logic, parser, or pipeline flow; no golden-set evals for Match Type.

---

## 7. Security & Operations — **B**

**Strengths:**
- Credentials path is parameterized; README mentions `config/credentials.json` and `.env`.
- No secrets in repo; dependency set is small and standard.

**Weaknesses:**
- No `.env.example` or doc of required env vars (e.g. for Gemini if used elsewhere).
- Profile path is machine-specific; no warning if profile file is missing (evaluator still runs with “Error: Master profile not found” in context).

---

## Summary Table

| Dimension | Grade | Notes |
|-----------|--------|------|
| Purpose alignment | A– | Delivers sourcing → filter → evaluate → Sheets; sponsorship broken. |
| Architecture | B+ | Clear layers; unused DB; sponsorship not integrated. |
| Code quality | B | Readable; several bugs and hardcoded paths. |
| Robustness | B | Incremental/batch behavior good; no retries; inefficient URL fetches. |
| Maintainability | B+ | Easy to add scrapers; no evals or config. |
| Testing | C+ | Tests present but broken imports and no regression/evals. |
| Security / Ops | B | Credentials external; env/config under-documented. |

**Overall: B–** — The app clearly serves the stated goal and is structured well enough to extend and fix. The main gaps are: (1) broken or inconsistent pieces (sponsorship, tests, parser regex), (2) no evaluation or calibration of the LLM output, and (3) efficiency and configuration choices that could have been better from the start. With the recent fixes (evals, calibration, efficiency, and bug fixes), the same codebase would sit in the **B+ / A–** range.

---

## List of changes (from the three gaps)

### 1. Broken or inconsistent pieces
| Change | Status |
|--------|--------|
| Fix sponsorship_agent: correct imports, wire `self.llm` (Gemini wrapper) | Done (earlier) |
| Fix parser regex: `**Skill Gap Summary**`, `**Reasoning**` | Done (earlier) |
| Fix tests: `src.core` / `src.agents` imports, remove `openai_client` reference | Done (earlier) |
| CONTRIBUTING typo: `evaluate_evals.py` → `evaluate_jobs.py` | Done below |
| Move `import re` to module top in `sourcing_agent.py` | Done below |

### 2. Evaluation and calibration of LLM output
| Change | Status |
|--------|--------|
| Eval harness: `eval/golden_jobs.json`, `eval/run_eval.py`, accuracy metric | Done (earlier) |
| Calibration summary after run: Match Type distribution, Maybe > 80% warning | Done (earlier) |
| Prompt: Match Type definitions, skill-count step, few-shot guidance, anti-Maybe default | Done (earlier) |
| Rule-based nudge: profile skill overlap ≥ 5 → at least Worth Trying; post-parse override | Done (earlier) |

### 3. Efficiency and configuration
| Change | Status |
|--------|--------|
| Run Community/Jobright/Arbeitnow/ATS once per pipeline | Done (earlier) |
| Parallel JobSpy (thread pool), single evaluation pass | Done (earlier) |
| Batch LLM evaluation (e.g. 4 jobs per call), Ollama HTTP API, URL cache, larger sheet batch | Done (earlier) |
| Config file for queries, locations, batch sizes, workers | Done below |
| `.env.example` and env for profile path / Ollama host / API keys | Done below |
| Profile path from config or env; startup check if profile missing | Done below |
| Update CONTRIBUTING: batch size 25, parallel sourcing | Done below |
