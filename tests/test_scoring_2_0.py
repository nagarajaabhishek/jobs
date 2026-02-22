"""
Scoring 2.0 & tiered verdicts: parse_evaluation, score_to_verdict, fallback score, and sheet sort.
Uses production helpers so tests fail on regression (assertions) and stay aligned with code.
"""
import pytest

from src.agents.evaluate_jobs import JobEvaluator, score_to_verdict
from src.core.google_sheets_client import GoogleSheetsClient


# ---- score_to_verdict (single source of truth) ----
def test_score_to_verdict_tiers():
    assert score_to_verdict(95) == "🔥 Auto-Apply"
    assert score_to_verdict(85) == "🔥 Auto-Apply"
    assert score_to_verdict(84) == "✅ Strong Match"
    assert score_to_verdict(70) == "✅ Strong Match"
    assert score_to_verdict(69) == "⚖️ Worth Considering"
    assert score_to_verdict(50) == "⚖️ Worth Considering"
    assert score_to_verdict(49) == "❌ No"
    assert score_to_verdict(0) == "❌ No"


# ---- parse_evaluation: score parsing ----
def test_parse_evaluation_score_and_verdict():
    evaluator = JobEvaluator()
    cases = [
        ("Apply Conviction Score: 95\nVerdict: 🔥 Auto-Apply", 95),
        ("Score: 78\nVerdict: ✅ Strong Match", 78),
        ("Apply Conviction Score: 55\nVerdict: ⚖️ Worth Considering", 55),
        ("Score: 20\nVerdict: ❌ No", 20),
    ]
    for raw_text, expected_score in cases:
        *_, score = evaluator.parse_evaluation(raw_text)
        assert score == expected_score, f"parse_evaluation({raw_text!r}) -> score {score}, expected {expected_score}"


def test_parse_evaluation_llm_failed_score_returns_zero():
    evaluator = JobEvaluator()
    raw = "No score provided here."
    *_, score = evaluator.parse_evaluation(raw)
    assert score == 0
    assert score_to_verdict(score) == "❌ No"


def test_parse_evaluation_return_structure():
    """Assert parse_evaluation returns exactly 9 values in documented order."""
    evaluator = JobEvaluator()
    raw = "Apply Conviction Score: 60\nVerdict: ⚖️ Worth Considering"
    result = evaluator.parse_evaluation(raw)
    assert len(result) == 9
    match_type, recommended, h1b, loc_ver, skills, reasoning, salary, tech_stack, score = result
    assert score == 60
    assert score_to_verdict(score) == "⚖️ Worth Considering"


# ---- full flow: parsed score -> verdict via production mapping ----
def test_parsed_score_maps_to_expected_verdict():
    evaluator = JobEvaluator()
    cases = [
        ("Apply Conviction Score: 95\nVerdict: 🔥 Auto-Apply", 95, "🔥 Auto-Apply"),
        ("Score: 78\nVerdict: ✅ Strong Match", 78, "✅ Strong Match"),
        ("Apply Conviction Score: 55\nVerdict: ⚖️ Worth Considering", 55, "⚖️ Worth Considering"),
        ("Score: 20\nVerdict: ❌ No", 20, "❌ No"),
    ]
    for raw_text, expected_score, expected_verdict in cases:
        *_, score = evaluator.parse_evaluation(raw_text)
        assert score == expected_score
        verdict = score_to_verdict(score)
        assert verdict == expected_verdict, f"score {score} -> {verdict}, expected {expected_verdict}"


# ---- fallback score (no LLM score) ----
def test_compute_fallback_score():
    evaluator = JobEvaluator()
    # No profile keywords / empty JD -> low score
    score_empty = evaluator._compute_fallback_score("", "Some City")
    assert 0 <= score_empty <= 80
    assert score_to_verdict(score_empty) in ("⚖️ Worth Considering", "❌ No")

    # Texas location adds +20
    score_texas = evaluator._compute_fallback_score("", "Arlington, TX")
    assert score_texas >= score_empty
    assert score_texas >= 20

    # JD with many profile keywords (if any) can push overlap up; we only assert bounds
    score_jd = evaluator._compute_fallback_score("Python agile scrum product roadmap", "Remote")
    assert 0 <= score_jd <= 80


# ---- Google Sheets sort: use production get_sort_key_for_row ----
def test_sort_by_apply_score_uses_production_logic():
    client = GoogleSheetsClient()
    headers = ["Status", "Title", "Company", "Loc", "URL", "Src", "Date", "Apply Score", "Match Type"]
    rows = [
        ["EVALUATED", "Job A", "C1", "L1", "U1", "S1", "D1", "55", "⚖️ Worth Considering"],
        ["EVALUATED", "Job B", "C2", "L2", "U2", "S2", "D2", "92", "🔥 Auto-Apply"],
        ["EVALUATED", "Job C", "C3", "L3", "U3", "S3", "D3", "78", "✅ Strong Match"],
        ["EVALUATED", "Job D", "C4", "L4", "U4", "S4", "D4", "10", "❌ No"],
    ]
    score_col_idx = headers.index("Apply Score")
    sorted_rows = sorted(rows, key=lambda row: client.get_sort_key_for_row(row, headers))
    sorted_scores = [row[score_col_idx] for row in sorted_rows]
    assert sorted_scores == ["92", "78", "55", "10"], (
        f"Sort should prioritize by Apply Score desc; got {sorted_scores}"
    )


def test_sort_emoji_verdicts_without_score_use_priority_map():
    """When Apply Score is missing (0), order by Match Type priority from SORT_PRIORITY_MAP."""
    client = GoogleSheetsClient()
    headers = ["Status", "Title", "Company", "Loc", "URL", "Src", "Date", "Apply Score", "Match Type"]
    rows = [
        ["EVALUATED", "Job A", "C1", "L1", "U1", "S1", "D1", "", "❌ No"],
        ["EVALUATED", "Job B", "C2", "L2", "U2", "S2", "D2", "", "🔥 Auto-Apply"],
        ["EVALUATED", "Job C", "C3", "L3", "U3", "S3", "D3", "", "⚖️ Worth Considering"],
    ]
    sorted_rows = sorted(rows, key=lambda row: client.get_sort_key_for_row(row, headers))
    match_col_idx = headers.index("Match Type")
    verdicts = [row[match_col_idx] for row in sorted_rows]
    # Auto-Apply (1) before Worth Considering (3) before No (5)
    assert verdicts[0] == "🔥 Auto-Apply"
    assert verdicts[1] == "⚖️ Worth Considering"
    assert verdicts[2] == "❌ No"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
