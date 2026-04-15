"""Preflight validates title_fit config when title_fit.enabled is true."""
from __future__ import annotations

import os
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.core.preflight import run_cycle_preflight  # noqa: E402


def test_preflight_skips_title_fit_when_disabled(monkeypatch):
    import apps.cli.legacy.core.config as cfg

    monkeypatch.setattr(
        cfg,
        "get_title_fit_config",
        lambda: {"enabled": False},
    )
    res = run_cycle_preflight(
        project_root=PROJECT_ROOT,
        require_gemini=False,
        require_google_credentials=False,
        require_dense_profile=False,
    )
    assert res.ok
    assert not any("title_fit" in e.lower() for e in res.errors)


def test_preflight_fails_when_enabled_and_user_file_missing(monkeypatch, tmp_path):
    import apps.cli.legacy.core.config as cfg

    monkeypatch.setattr(
        cfg,
        "get_title_fit_config",
        lambda: {"enabled": True, "llm_disambiguation_enabled": False},
    )
    monkeypatch.setattr(
        "apps.cli.legacy.core.title_fit_gate.title_fit_user_yaml_path",
        lambda project_root=None: str(tmp_path / "missing_title_fit_user.yaml"),
    )
    res = run_cycle_preflight(
        project_root=PROJECT_ROOT,
        require_gemini=False,
        require_google_credentials=False,
        require_dense_profile=False,
    )
    assert not res.ok
    assert any("title_fit_user.yaml" in e for e in res.errors)


def test_preflight_fails_when_learned_blocks_enabled_but_file_missing(monkeypatch, tmp_path):
    import apps.cli.legacy.core.config as cfg

    monkeypatch.setattr(
        cfg,
        "get_sourcing_config",
        lambda: {
            "apply_learned_title_blocks": True,
            "learned_title_blocks_path": str(tmp_path / "nonexistent_learned.yaml"),
        },
    )
    res = run_cycle_preflight(
        project_root=PROJECT_ROOT,
        require_gemini=False,
        require_google_credentials=False,
        require_dense_profile=False,
        check_title_fit_when_enabled=False,
    )
    assert not res.ok
    assert any("learned title blocks" in e.lower() for e in res.errors)


def test_preflight_check_can_be_disabled(monkeypatch, tmp_path):
    import apps.cli.legacy.core.config as cfg

    monkeypatch.setattr(
        cfg,
        "get_title_fit_config",
        lambda: {"enabled": True, "llm_disambiguation_enabled": False},
    )
    monkeypatch.setattr(
        "apps.cli.legacy.core.title_fit_gate.title_fit_user_yaml_path",
        lambda project_root=None: str(tmp_path / "missing.yaml"),
    )
    res = run_cycle_preflight(
        project_root=PROJECT_ROOT,
        require_gemini=False,
        require_google_credentials=False,
        require_dense_profile=False,
        check_title_fit_when_enabled=False,
    )
    assert res.ok
