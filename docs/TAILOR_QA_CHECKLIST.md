# TailorAgent QA checklist (productization)

Pipeline tailoring uses [`core_agents/resume_agent/tailor.py`](../core_agents/resume_agent/tailor.py). Settings come from `evaluation.*` and `resume.*` in [`config/pipeline.yaml`](../config/pipeline.yaml).

## Config gates

| Setting | Role |
|---------|------|
| `evaluation.tailor_min_score` | Minimum Apply Score to run tailoring from pipeline (`run_pipeline.py` tailor phase). |
| `evaluation.tailor_max_qa_attempts` | LLM + deterministic QA repair iterations. |
| `evaluation.tailor_stagnation_limit` | Stop if the same QA signature repeats without improvement. |
| `resume.profile`, `resume.base_role_yaml`, `resume.agent_dir` | Profile folder and base role YAML under the resume agent tree. |

## Manual JD workflow (sheet-first)

1. Use tab named by `sheet.manual_jd_tailor_tab` (default `Manual_JD_Tailor`).
2. Paste URLs / set `Recommended Resume` as documented in the root [README.md](../README.md).
3. Run the tailor CLI entrypoint described in README (`--from-tailor-tab` or project script).

## QA gates (anti-fabrication)

- [ ] **Source YAML only:** Edits must come from LLM output applied to cloned role YAML; no silent invention of employers or metrics.
- [ ] **Forbidden phrasing:** Deterministic replacements in `TailorAgent` reduce generic resume filler; verify final PDF reads naturally.
- [ ] **`GENERATED_PENDING_REVIEW`:** Sheet status after generation; human review before marking applied.
- [ ] **Evidence alignment:** Tailored bullets should align with evaluation `Evidence JSON` and skill gaps where applicable.

## Failure handling

If LaTeX or generation subprocess fails, check console logs under the tailor phase; partial rows should remain revertible via sheet status columns (see `GoogleSheetsClient.update_resume_for_row` usage in `run_pipeline.py`).
