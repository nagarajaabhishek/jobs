# Job Automation Pipeline

An automated system for sourcing, filtering, and evaluating job postings using **Gemini 1.5 Pro** and **OpenRouter (Unified Cloud)**.

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

    subgraph Logic ["3. Evaluation Layer (Cloud)"]
        G[Evaluation Agent] --> M[LLM Router]
        M -- Primary --> N[Gemini 1.5 Pro API]
        M -- Alternative --> O[OpenRouter / Cloud Bridge]
        N & O --> Q[Match Scoring 2.0 Rubric]
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
- **Dual-Model Strategy**:
    - **Sourcing/Sniffing**: Powered by `gemini-2.5-flash-lite` for ultra-low-cost relevance checks.
    - **Deep Matching**: Powered by `gemini-2.0-flash` for high-fidelity evaluation and scoring.
- **Unified Cloud Bridge**: One API key (OpenRouter) to access any model (Claude, DeepSeek, Gemini).
- **AI-Enhanced Sourcing**: 
    - **Smart Sniffing**: Drops irrelevant roles before they hit the sheet.
    - **Query Expansion**: Brainstorms search terms for better coverage.
- **Cloud-Powered Performance**: Deep evaluation with robust 429 rate limit resilience.

## Project Structure
- `src/agents/`: Business logic (Sourcing, Evaluation).
- `src/core/`: Shared clients (Sheets, `LLMRouter`, Config).
- `src/scrapers/`: Individual job site scrapers.
- `src/prompts/`: LLM System Prompts.
- `scripts/`: Utility scripts categorized into `diagnostics/`, `tools/`, and `legacy/`.
- `config/`: Credentials, `pipeline.yaml`, and local JD cache.
- `data/`: Profiles, Master Context, and harvested insights.

## Usage
Run the full pipeline:
```bash
python3 run_pipeline.py
```
For detailed agent instructions, see [.agent/workflows/job_pipeline.md](.agent/workflows/job_pipeline.md).

## Configuration
- **Environment**: Copy `.env.example` to `.env`. Required: `OPENROUTER_API_KEY`, `GEMINI_API_KEY` (fallback).
- **Pipeline**: Edit `config/pipeline.yaml` to change:
    - `sourcing`: Queries, `expand_ai_queries`, `use_ai_filter`.
    - `evaluation`: `provider` (openrouter/gemini), `gemini_model`, `openrouter_model`.

## Job descriptions (JD)
- **Local cache**: Full JDs are stored in `config/jd_cache.json` (keyed by canonical URL) to avoid cluttering Google Sheets while keeping evaluation context high.

## Sorting & Verdicts
- **SSOT**: Sorting logic is centralized around a 0-100 "Apply Conviction Score". High scores (🔥/✅) are sorted to the top automatically.
