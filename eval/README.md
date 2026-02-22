# Match Type Eval

Hand-labeled golden jobs and a script to measure how well the evaluator predicts **Match Type**.

## Setup

Run from project root:

```bash
python eval/run_eval.py
```

## Golden dataset

- `golden_jobs.json`: list of jobs with `title`, `company`, `location`, `description`, and **expected_match_type** (For sure / Worth Trying / Ambitious / Maybe / Not at all).
- Add or edit entries to match your profile and target roles so the eval reflects real calibration.

## Metrics

- **Accuracy**: % of jobs where predicted Match Type equals expected.
- **By expected Match Type**: correct / total per label (surfaces over-use of "Maybe" or misclassifications).

Use these to tune the prompt or the 5+ skill-overlap nudge.
