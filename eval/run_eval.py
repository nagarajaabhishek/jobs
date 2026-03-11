"""
Eval harness for Match Type: run the job evaluator on golden (hand-labeled) jobs
and report accuracy and per-class metrics.
"""
import json
import os
import sys
from pathlib import Path
from typing import Optional, Union

# Robust Project root discovery
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

try:
    from dotenv import load_dotenv
    load_dotenv(root / ".env")
except ImportError:
    pass

from src.agents.evaluate_jobs import JobEvaluator, score_to_verdict


def map_verdict_to_golden(verdict: str) -> str:
    """Maps new emoji-based verdicts to legacy golden labels for evaluation."""
    v = verdict.lower()
    if "must-apply" in v or "🚀" in v:
        return "For sure"
    if "strong match" in v or "✅" in v:
        return "Worth Trying"
    if "ambitious" in v or "⚡" in v:
        return "Ambitious"
    if "worth" in v or "⚖️" in v or "low priority" in v or "📉" in v:
        return "Maybe"
    if "no" in v or "❌" in v:
        return "Not at all"
    return "Maybe"


def load_golden(path: Optional[Union[str, Path]] = None):
    if path is None:
        path = Path(__file__).resolve().parent / "golden_jobs.json"
    with open(path, "r") as f:
        return json.load(f)


def normalize_match_type(s):
    return (s or "").strip().lower().replace(" ", "")


def run_eval(golden_path=None, verbose=True):
    golden = load_golden(golden_path)
    evaluator = JobEvaluator()
    sys_prompt = evaluator.load_system_prompt()
    profiles_prompt = evaluator.load_user_profiles()
    grounded_sys_prompt = f"{sys_prompt}\n\n### USER PROFILE SUMMARY (GROUND TRUTH)\n{profiles_prompt}"
    profile_keywords = evaluator.get_profile_skill_keywords()

    results = []
    for i, job in enumerate(golden):
        title = job.get("title", "")
        company = job.get("company", "")
        location = job.get("location", "")
        desc = job.get("description", "")
        expected = job.get("expected_match_type", "")

        job_context = (
            f"Job Title: {title}\nCompany: {company}\nLocation: {location}\nJob Description: {desc}"
        )
        jd_text = desc
        overlap = evaluator.count_skill_overlap(jd_text, profile_keywords)
        if overlap >= 5:
            job_context += "\n[Pre-check: This JD contains 5+ skills from the profile. You MUST rate at least Worth Trying. Do NOT use Maybe.]"

        raw_text, engine = evaluator.llm.generate_content(
            system_prompt=grounded_sys_prompt,
            user_prompt=f"### JOB POSTING TO EVALUATE\n{job_context}",
        )
        if engine == "FAILED":
            predicted = "Maybe"
        else:
            match_type, _, _, _, _, _, _, _, score = evaluator.parse_evaluation(raw_text)
            
            # Use unified scoring logic
            if score == 0:
                score = evaluator._compute_fallback_score(jd_text, location)
            
            verdict = score_to_verdict(score)
            predicted = map_verdict_to_golden(verdict)
            
            if overlap >= 5 and predicted in ["Maybe", "Not at all"]:
                predicted = "Worth Trying"

        expected_n = normalize_match_type(expected)
        predicted_n = normalize_match_type(predicted)
        # Treat "forsure" vs "for sure" etc.
        if "forsure" in expected_n or "for sure" in expected_n:
            expected_n = "forsure"
        if "forsure" in predicted_n or "for sure" in predicted_n:
            predicted_n = "forsure"
        if "worthtrying" in expected_n or "worth trying" in expected_n:
            expected_n = "worthtrying"
        if "worthtrying" in predicted_n or "worth trying" in predicted_n:
            predicted_n = "worthtrying"
        if "notatall" in expected_n or "not at all" in expected_n:
            expected_n = "notatall"
        if "notatall" in predicted_n or "not at all" in predicted_n:
            predicted_n = "notatall"

        correct = expected_n == predicted_n
        results.append(
            {
                "title": title,
                "expected": expected,
                "predicted": predicted,
                "correct": correct,
                "overlap": overlap,
            }
        )
        if verbose:
            status = "✓" if correct else "✗"
            print(f"  {status} {title[:40]}... → expected={expected}, predicted={predicted}, overlap={overlap}")

    # Metrics
    correct_count = sum(1 for r in results if r["correct"])
    total = len(results)
    accuracy = (100 * correct_count / total) if total else 0

    # Per-class: precision/recall would need a fixed set of labels; here we just show confusion-style counts
    from collections import defaultdict
    by_expected = defaultdict(list)
    for r in results:
        by_expected[r["expected"]].append(r["correct"])
    print("\n--- Eval results ---")
    print(f"Accuracy: {correct_count}/{total} = {accuracy:.1f}%")
    print("By expected Match Type (correct / total):")
    for label in ["For sure", "Worth Trying", "Ambitious", "Maybe", "Not at all"]:
        if label in by_expected:
            correct_l = sum(by_expected[label])
            total_l = len(by_expected[label])
            print(f"  {label}: {correct_l}/{total_l}")

    return {"accuracy": accuracy, "correct": correct_count, "total": total, "results": results}


if __name__ == "__main__":
    run_eval()
