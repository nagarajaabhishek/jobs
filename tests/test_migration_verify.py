"""Regression: evaluator can load grounded profile context (dense matrix)."""

import os

import pytest

from apps.cli.legacy.agents.evaluate_jobs import JobEvaluator


def test_migration_dense_matrix_loads():
    matrix_path = os.path.join(os.getcwd(), "data", "dense_master_matrix.json")
    if not os.path.isfile(matrix_path):
        pytest.skip(f"Missing {matrix_path} (run build_dense_matrix if needed)")

    evaluator = JobEvaluator()
    content = evaluator.load_user_profiles()
    assert "## CANDIDATE DENSE MATRIX" in content
    assert "TARGET ROLES AVAILABLE" in content
