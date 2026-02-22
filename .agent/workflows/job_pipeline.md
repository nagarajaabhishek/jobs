---
description: How to run the job sourcing and evaluation pipeline
---

# Job Pipeline Workflow
// turbo-all

Follow these steps to perform a complete job sourcing and evaluation run for today.

1. **Prerequisites**
   - Ensure Ollama is running (`ollama serve`).
   - Ensure `.env` contains necessary configuration.
   - Ensure `config/credentials.json` is present for Google Sheets.

2. **Run Sourcing & Evaluation**
   // turbo
   Execute the central pipeline script:
   ```bash
   python3 run_pipeline.py
   ```

3. **Verify Results**
   - Check the Google Sheet "Resume_Agent_Jobs" under today's date tab.
   - Confirm jobs are marked as "EVALUATED".
   - Confirm "Match Type" and "Recommended Resume" are populated.

4. **Refine Results (Optional)**
   - If results are too broad, adjust `queries` in `run_pipeline.py` or filters in `src/agents/sourcing_agent.py`.
