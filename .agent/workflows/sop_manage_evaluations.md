---
description: How to manage evaluations and migrate "stashed" tags.
---

# SOP: Evaluation Management

This SOP covers migrating evaluations from metadata tags to structured sheet columns and re-evaluating "Maybe" jobs.

### 1. Detect Stashed Evaluations
Check if jobs have evaluation data in the "Sourcing Tags" column but are still marked as `NEW`.
// turbo
```bash
python3 scripts/diagnostics/inspect_tags.py
```

### 2. Migrate Evaluations (Skip Redundancy)
Migrate stashed evaluations to the structured columns to avoid re-processing fees/time.
// turbo
    python3 scripts/diagnostics/migrate_sourcing_evals.py

### 3. Re-evaluate "Maybe" Jobs
Target existing "Maybe" ratings in the sheet to upgrade them with more context or updated prompts.
// turbo
```bash
python3 scripts/tools/re_evaluate_maybes.py
```

### 4. Verify Final Sheet Status
Confirm the counts of `EVALUATED` vs `NEW` jobs.
// turbo
```bash
python3 scripts/diagnostics/count_by_status.py
```
