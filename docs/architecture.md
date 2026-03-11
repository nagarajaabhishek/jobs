# System Architecture

This document describes the high-level architecture of the Job Search Automation pipeline. The pipeline is designed around a 4-layer architecture: Sourcing, Storage, Evaluation, and Output.

## Core Layers

### 1. Sourcing Layer
The sourcing layer is responsible for aggregating job listings from disparate sources. It uses active scrapers (e.g., JobSpy) and ATS-specific scrapers (e.g., Greenhouse, Ashby, Lever). Configuration for active queries and limits is handled in `config/pipeline.yaml`.

### 2. Storage & Deduplication Layer
Handles storing fetched jobs, detecting duplicates using URL normalization, and managing the local JD Cache (`data/jd_cache.json`).

### 3. Evaluation Layer
The "Brain" of the pipeline. Job Descriptions (JDs) are passed to an LLM `evaluate_jobs.py` which uses contextual profiles (e.g., Master Context, Role Specializations) to perform "Deep Matching" and calculate an Apply Conviction Score.

### 4. Output Layer
The final results are exported. Job data is batched and streamed directly to a Google Sheet (`google_sheets_client.py`).

## Architecture Diagram

```mermaid
graph TD
    %% Base Infrastructure
    Config[(pipeline.yaml)]
    GoogleSheets[Google Sheets]

    %% Sourcing Layer
    subgraph Sourcing Layer
        JobSpy[JobSpy Scraper]
        Community[Community Scraper]
        ATSScraper[ATS Scraper]
        JobRight[JobRight Scraper]
        RemoteOK[RemoteOK Scraper]
        ArbeitNow[ArbeitNow Scraper]
    end

    %% Storage Layer
    subgraph Storage Layer
        Filters[Job Filters & Deduplication]
        JDCache[(JD Cache / Local DB)]
    end

    %% Evaluation Layer
    subgraph Evaluation Layer
        SourcingAgent((Sourcing Agent))
        EvalAgent((Evaluation Agent))
        SponsorshipAgent((Sponsorship Agent))
        LLMRouter{LLM Router - Gemini/OpenRouter}
    end

    %% Data Flow
    Config -.-> SourcingAgent
    JobSpy --> SourcingAgent
    ATSScraper --> SourcingAgent
    Community --> SourcingAgent
    JobRight --> SourcingAgent
    RemoteOK --> SourcingAgent
    ArbeitNow --> SourcingAgent

    SourcingAgent --> Filters
    Filters --> JDCache
    JDCache --> EvalAgent

    EvalAgent --> LLMRouter
    SponsorshipAgent --> EvalAgent

    %% Output
    EvalAgent --> GoogleSheets
```

---

## Dynamic Architecture Generator

As the pipeline evolves, this static diagram may become outdated. You can dynamically generate an updated architecture diagram by running the included python utility:

```bash
python scripts/tools/generate_architecture.py
```

This script will read the active scrapers, agents, and configuration, and output a fresh Mermaid diagram directly to the terminal, which you can paste here or view in any Markdown renderer.
