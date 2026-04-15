# Agent Commands Reference

Single place for commonly used agent/pipeline commands and key flags.

## 1) Tailor From Manual Sheet (recommended daily command)

```bash
python3 scripts/tools/tailor_from_urls.py --from-tailor-tab
```

Behavior with this command:
- auto-ensures `Manual_JD_Tailor` tab exists
- reads URLs + `Recommended Resume` from sheet
- runs tailoring + QA loop
- writes sheet result columns (`Status`, `Last processed`, `Tailored YAML`, `Error`)
- runs variant validation (tailored vs generic recommended) and writes winner columns

### Useful flags
- `--skip-tailor-validation`  
  Generate YAML only (skip QA/LaTeX/PDF).
- `--also-eval`  
  Run job-fit evaluator first; evaluator recommendation can override sheet recommendation.
- `--json`  
  Print machine-readable JSON per URL.
- `--no-validate-variants`  
  Disable post-tailor tailored-vs-generic comparison.
- `--profile <name>`  
  Override resume profile.
- `--base-yaml <filename>`  
  Override base role YAML.

---

## 2) Tailor Direct URLs

```bash
python3 scripts/tools/tailor_from_urls.py "https://..." "https://..."
```

### Optional
- `--file urls.txt`
- `--skip-tailor-validation`
- `--validate-variants` (off by default for direct URL mode)

---

## 3) Evaluate Job URLs Only

```bash
python3 apps/cli/scripts/tools/eval_test_urls.py --file urls.txt
```

Use this for evaluation diagnostics without full tailoring pipeline.

---

## 4) ATS Scoring Utility (PDF vs JD txt)

```bash
python3 scripts/tools/ats_score.py <path_to_resume_pdf> <path_to_jd_txt>
```

Use this for standalone ATS-like similarity checks.

---

## 5) Pipeline Run (legacy orchestrated flow)

```bash
python3 apps/cli/run_pipeline.py
```

Uses `config/pipeline.yaml` settings for sourcing/evaluation/tailoring orchestration.

