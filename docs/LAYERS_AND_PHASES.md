# Layers, phases, and the SSOT trio

This document ties together three sources of truth so engineering, ops, and product stay aligned:

| Document | Purpose |
|----------|---------|
| [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) | Non-negotiable boundaries (no fabrication, no eval without verified JD + compiled context, auditability). |
| [CYCLE_SSOT.md](CYCLE_SSOT.md) | Authoritative per-job lifecycle diagram (regenerate with `python apps/cli/scripts/tools/generate_cycle_ssot.py` after pipeline changes). |
| This file | Layer stack + build phases + where code lives. |

## Layer model

```mermaid
flowchart TB
  subgraph presentation [Presentation]
    UI[Web_UI_Marketing_and_Future_App]
    API[API_Webhooks_SSE]
  end

  subgraph orchestration [Orchestration]
    Pipeline[run_pipeline_and_CycleHooks]
    WF[WorkflowRegistry_SOPs]
  end

  subgraph agents [Agents_and_Intelligence]
    SA[SourcingAgent]
    JE[JobEvaluator_StrictJSON]
    TA[TailorAgent]
    CSA[CareerStrategyAgent_optional]
    LLM[LLMRouter]
  end

  subgraph data_plane [Data_and_Context]
    Profile[master_context_and_dense_master_matrix]
    JDC[jd_cache_and_JD_verification]
    Sheets[Google_Sheets_SSOT_rows]
    Learn[learned_patterns_calibration]
  end

  subgraph sourcing_net [Sourcing_Network]
    Scrapers[JobSpy_JobRight_ATS_Remotive_etc]
  end

  subgraph infra [Infrastructure]
    Config[config_pipeline_yaml_credentials_env]
    Preflight[PreflightChecks]
  end

  infra --> orchestration
  sourcing_net --> SA
  SA --> data_plane
  data_plane --> JE
  JE --> LLM
  JE --> data_plane
  TA --> data_plane
  CSA --> data_plane
  orchestration --> agents
  presentation -.-> API
  API -.-> orchestration
```

## Build phases (dependency order)

```mermaid
flowchart LR
  P1[Phase1_Foundation]
  P2[Phase2_PipelineSpine]
  P3[Phase3_LearningLoop]
  P4[Phase4_TailorProduct]
  P5[Phase5_AppLayer]
  P6[Phase6_ConversationalThara]

  P1 --> P2 --> P3 --> P4 --> P5 --> P6
```

- **Phase 1–2:** Contract + hardened CLI pipeline ([`apps/cli/run_pipeline.py`](../apps/cli/run_pipeline.py)).
- **Phase 3:** Cycle hooks and calibration ([`docs/CYCLE_HOOKS.md`](CYCLE_HOOKS.md)).
- **Phase 4:** Tailor + QA ([`docs/TAILOR_QA_CHECKLIST.md`](TAILOR_QA_CHECKLIST.md)).
- **Phase 5:** API + app shell ([`apps/api/README.md`](../apps/api/README.md), [`website_ui/`](../website_ui/)).
- **Phase 6:** Roadmap ([`docs/ROADMAP_THARA_ADVANCED.md`](ROADMAP_THARA_ADVANCED.md)).

## Canonical imports

Production pipeline code lives under **`apps/cli/legacy/`** and **`core_agents/`**. The older **`src/`** tree remains for legacy scripts and tests; see [CANONICAL_IMPORTS.md](CANONICAL_IMPORTS.md).
