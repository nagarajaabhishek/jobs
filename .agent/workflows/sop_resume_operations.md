---
description: How to compile resumes and run ATS scoring utilities.
---

# SOP: Resume Operations

This SOP outlines the procedures for compiling LaTeX resumes into PDFs and scoring them against job descriptions.

### 1. ATS Matching & Scoring
Use the scoring tool to evaluate a specific resume against a job description.
// turbo
```bash
python3 scripts/tools/ats_score.py --resume target_resume.pdf --jd job_description.txt
```

### 2. Batch Compilation
If you have multiple LaTeX resumes, use the shell script to compile them all.
// turbo
```bash
bash scripts/tools/compile_resume.sh
```

### 3. Verification of Results
Ensure the "Recommended Resume" column in Google Sheets matches your specialized resume family (PM, PO, BA, etc.).
// turbo
```bash
python3 scripts/diagnostics/inspect_rows.py
```

### Troubleshooting
- **LaTeX Compilation Fail**: Ensure `pdflatex` or `tectonic` is installed and in your PATH.
- **Scoring mismatch**: Check `src/core/prompt_templates.py` to ensure the scoring criteria align with your latest professional context.
