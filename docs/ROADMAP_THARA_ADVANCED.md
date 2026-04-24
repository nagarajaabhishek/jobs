# Roadmap: conversational ingestion, RAG, interview and outreach

This tracks **Phase 6** from [LAYERS_AND_PHASES.md](LAYERS_AND_PHASES.md). Nothing here is a commitment to ship order; it extends the [Thara implementation plan](../website_ui/Thara_App_Planning/THARA_IMPLEMENTATION_PLAN.md).

## Conversational master context

**Goal:** Replace YAML-only edits with guided chat + uploads while preserving [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) (compiled `master_context.yaml` + `dense_master_matrix.json` as audit artifacts).

**Building blocks:** Auth (`apps/api` placeholder pattern), structured extraction prompts, and validation gates before merging into context files.

## Vector / RAG memory (optional)

**Goal:** Semantic retrieval over projects and JD history.

**Requirements:** Data residency, deletion policy, and cost controls for embedding APIs. Keep RAG **off** the critical path until the baseline pipeline is stable.

## Interview and outreach agents

**Goal:** STAR-style prep and outreach templates grounded in evaluated JD + profile.

**Near-term (no new agents required):** Use templates under [`data/career_ops_templates/`](../data/career_ops_templates/) and fill from sheet exports or digest JSON.

**Later:** Dedicated `InterviewAgent` / `OutreachAgent` modules behind the same API as [`apps/api`](../apps/api/README.md), with explicit human approval before send.

## Orchestration

If you adopt LangGraph or GADK, treat [`apps/cli/run_pipeline.py`](../apps/cli/run_pipeline.py) as the **batch** orchestrator and add conversational flows as separate graphs that call the same `JobEvaluator` / `TailorAgent` primitives to avoid duplicate business logic.
