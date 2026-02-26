---
description: How to enrich job data with missing sponsorship or salary info.
---

# SOP: Data Enrichment (H1B & Salary)

Use this procedure when top matches (`Auto-Apply` or `Strong Match`) are missing critical data like H1B Sponsorship status or Salary ranges.

### 1. Identify Data Gaps
Check which high-priority jobs are missing sponsorship info.
// turbo
```bash
python3 scripts/diagnostics/check_jd_for_h1b.py
```

### 2. Run Enrichment Pass
Run the enrichment script which specifically fetches JDs for top matches and asks Ollama for sponsorship/salary specifics.
// turbo
```bash
python3 scripts/tools/fix_h1b.py
```

### 3. Verify Results
Check the `H1B Sponsorship` column in the Google Sheet for your top 10 matches.
// turbo
```bash
python3 scripts/tools/summarize_matches.py
```

### Why does this happen?
- **AGGREGATOR BLINDNESS**: Sources like Jobright (GitHub) often provide a summary but not the full JD. This SOP forces a second-look at the original job page for your highest conviction roles.
