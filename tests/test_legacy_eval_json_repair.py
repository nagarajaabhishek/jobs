"""Regression: legacy JobEvaluator.parse_evaluation repairs invalid JSON when reasoning contains raw newlines."""

from apps.cli.legacy.agents.evaluate_jobs import JobEvaluator, _repair_reasoning_json_newlines


def test_repair_reasoning_json_newlines_collapses_inner_breaks():
    blob = (
        '{"reasoning": "a\nb", "salary_range": "x", "location_verification": "USA", '
        '"h1b_sponsorship": "Unknown", "recommended_resume": "Product Manager (TPM)", '
        '"tech_stack": [], "skill_gaps": [], "apply_conviction_score": 40, '
        '"verdict": "Worth Considering", "score_breakdown": {}, "evidence": [], '
        '"confidence": 0.5, "jd_quality": "high", "output_quality": "high"}'
    )
    assert "\n" in blob.split('"reasoning": "')[1].split('", "salary_range"')[0]
    fixed = _repair_reasoning_json_newlines(blob)
    assert "\n" not in fixed.split('"reasoning": "')[1].split('", "salary_range"')[0]
    import json

    json.loads(fixed)


def test_parse_evaluation_repairs_multiline_reasoning():
    blob = (
        'Prefix\n{"location_verification": "USA", "h1b_sponsorship": "Unknown", '
        '"recommended_resume": "Product Manager (TPM)", "reasoning": "hello\nworld second", '
        '"salary_range": "Not mentioned", "tech_stack": [], "skill_gaps": [], '
        '"apply_conviction_score": 50, "verdict": "Worth Considering", '
        '"score_breakdown": {"skill_match": 50, "role_fit": 0, "strategic_priority": 0, '
        '"sponsorship": 0, "experience_gap_adjustment": 0}, '
        '"evidence": [], "confidence": 0.5, "jd_quality": "high", "output_quality": "high"}'
    )
    ev = JobEvaluator()
    _mt, _rec, _h1b, _loc, _gaps, reasoning, _sal, _ts, score = ev.parse_evaluation(blob)
    assert score == 50
    assert "hello" in reasoning and "world" in reasoning
    assert "\n" not in reasoning
