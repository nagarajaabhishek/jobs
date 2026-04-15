"""Regression: core evaluator caches and prompt pieces load without error."""

import os

import pytest

from apps.cli.legacy.agents.evaluate_jobs import JobEvaluator


def test_optimizations_evaluator_grounding():
    matrix_path = os.path.join(os.getcwd(), "data", "dense_master_matrix.json")
    if not os.path.isfile(matrix_path):
        pytest.skip(f"Missing {matrix_path}")

    evaluator = JobEvaluator()
    assert isinstance(evaluator.sponsors, dict)
    assert evaluator.get_strategic_priority("Dallas, TX")
    sys_prompt = evaluator.load_system_prompt()
    assert len(sys_prompt) > 200
    profiles = evaluator.load_user_profiles()
    assert "CANDIDATE DENSE MATRIX" in profiles
    final_grounded = (
        f"{sys_prompt}\n\n### USER PROFILE SUMMARY\n{profiles}"
    )
    assert "USER PROFILE SUMMARY" in final_grounded
