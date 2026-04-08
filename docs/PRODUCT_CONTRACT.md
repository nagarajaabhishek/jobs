# Product Contract (Engineering SSOT)

This document is the **engineering source of truth** for the product’s mission, boundaries, and non-negotiable constraints.
If code behavior conflicts with this contract, **the code must change**.

## Mission
Provide an end-to-end job sourcing + evaluation + improvement loop that is **grounded in real user evidence** and **real job descriptions**, enabling users to:
- decide whether to apply,
- choose the correct resume/profile,
- and receive prescriptive gap/upskilling guidance without fabrication.

## Purpose
- Reduce job search fatigue by automatically collecting relevant opportunities.
- Evaluate fit against the user’s verified context (profile, proof-of-work).
- Produce auditable feedback that can be reused for resume iteration and upskilling.

## Non-negotiable boundaries (Absolute Truth)
1. **No fabrication**: The system must not invent skills, tools, metrics, employers, titles, or outcomes.\n   - If information is missing, output a missing/unknown state.\n2. **No evaluation without user context**: Evaluation must fail fast if the user’s compiled profile context is missing/stale.\n3. **No evaluation without verified JD**: Evaluation must only run when the pipeline has the **actual JD text** extracted from known JD containers/selectors.\n   - Full-page text fallback is not acceptable for evaluation.\n4. **Auditability required**: Every score/verdict must be explainable with evidence.\n   - Store `Evidence JSON` in Sheets.\n5. **Honest confidence**: When JD/profile/model output is low-quality, the system must downgrade confidence and/or route to `NEEDS_REVIEW`.\n
## Required user context artifacts
- Source of truth: `master_context.yaml`\n- Compiled context: `dense_master_matrix.json` (must be fresher than `master_context.yaml` and role variants)\n
## Canonical states
- `NEW`: Ready for evaluation (verified JD present).\n- `NO_JD`: JD could not be verified via selector extraction; do not evaluate.\n- `EVALUATED`: Evaluation complete.\n- `NEEDS_REVIEW`: Model output invalid/incomplete; requires rerun or manual review.\n
## Definition of “cycle success”
- Jobs sourced and written with correct statuses.\n- Only verified-JD jobs are evaluated.\n- Each evaluated job includes:\n  - Match Type + Apply Score\n  - Evidence JSON (breakdown + JD quotes + profile evidence)\n- High-scoring jobs optionally go through tailoring with anti-fabrication guardrails.\n
