"""Tests for title_fit_gate (multi-track title/seniority gate)."""
from __future__ import annotations

import os
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.core.title_fit_gate import (  # noqa: E402
    evaluate_title_fit,
    load_all_track_definitions,
    merge_track_with_user_overrides,
    pick_best_track,
)


@pytest.fixture
def sample_tracks():
    return load_all_track_definitions()


@pytest.fixture
def base_user():
    return {
        "active_tracks": ["product_management", "business_analysis"],
        "effective_yoe": 2.0,
        "first_formal_role_flags": {
            "has_titled_pm_role": False,
            "has_titled_ba_role": False,
            "has_titled_program_project_role": False,
        },
        "policy": "conservative",
        "extra_block_tokens": [],
        "extra_prefer_tokens": [],
    }


def test_pick_best_track_prefers_more_specific_match(sample_tracks):
    active = ["product_management", "business_analysis"]
    t = pick_best_track("associate product manager", active, sample_tracks)
    assert t == "product_management"
    t2 = pick_best_track("senior business analyst", active, sample_tracks)
    assert t2 == "business_analysis"


def test_merge_user_extra_block(sample_tracks):
    t = sample_tracks["product_management"]
    u = {"extra_block_tokens": ["meta"], "extra_prefer_tokens": []}
    m = merge_track_with_user_overrides(t, u)
    assert "meta" in m["block_title_tokens"]


def test_merge_internship_opt_in(sample_tracks):
    t = sample_tracks["product_management"]
    off = merge_track_with_user_overrides(t, {"include_internship_entry_signals": False})
    assert "intern" not in off["prefer_title_tokens"]
    assert "internship" not in off["prefer_title_tokens"]
    on = merge_track_with_user_overrides(t, {"include_internship_entry_signals": True})
    assert "intern" in on["prefer_title_tokens"]
    assert "internship" in on["prefer_title_tokens"]


def test_merge_strips_intern_from_extra_prefer_when_disabled(sample_tracks):
    t = sample_tracks["product_management"]
    m = merge_track_with_user_overrides(
        t,
        {"include_internship_entry_signals": False, "extra_prefer_tokens": ["intern", "junior"]},
    )
    assert "intern" not in m["prefer_title_tokens"]
    assert "junior" in m["prefer_title_tokens"]


def test_plain_product_manager_rejected_when_untitled(sample_tracks, base_user):
    cfg = {"enabled": True, "require_track_match": True, "ambiguous_default": "reject"}
    ok, reason, _ = evaluate_title_fit(
        "Product Manager",
        "Own roadmap and stakeholders.",
        title_fit_cfg=cfg,
        user=base_user,
        all_tracks=sample_tracks,
    )
    assert not ok
    assert "entry signal" in reason


def test_associate_product_manager_passes(sample_tracks, base_user):
    cfg = {"enabled": True, "require_track_match": True, "ambiguous_default": "reject"}
    ok, reason, d = evaluate_title_fit(
        "Associate Product Manager",
        "",
        title_fit_cfg=cfg,
        user=base_user,
        all_tracks=sample_tracks,
    )
    assert ok
    assert d.get("track_id") == "product_management"


def test_senior_blocked(sample_tracks, base_user):
    cfg = {"enabled": True, "require_track_match": True, "ambiguous_default": "reject"}
    ok, reason, _ = evaluate_title_fit(
        "Senior Product Manager",
        "",
        title_fit_cfg=cfg,
        user=base_user,
        all_tracks=sample_tracks,
    )
    assert not ok
    assert "blocked token" in reason


def test_yoe_requirement_in_snippet(sample_tracks, base_user):
    cfg = {"enabled": True, "require_track_match": True, "ambiguous_default": "reject"}
    u = dict(base_user)
    u["first_formal_role_flags"] = dict(u["first_formal_role_flags"])
    u["first_formal_role_flags"]["has_titled_pm_role"] = True
    ok, reason, _ = evaluate_title_fit(
        "Product Manager",
        "Minimum 8 years of product management experience required.",
        title_fit_cfg=cfg,
        user=u,
        all_tracks=sample_tracks,
    )
    assert not ok
    assert "YOE" in reason or "years" in reason.lower()


def test_disabled_gate_always_passes(sample_tracks, base_user):
    cfg = {"enabled": False, "require_track_match": True}
    ok, _, d = evaluate_title_fit(
        "Senior Product Manager",
        "",
        title_fit_cfg=cfg,
        user=base_user,
        all_tracks=sample_tracks,
    )
    assert ok
    assert d.get("skipped") == "disabled"


def test_no_matching_track_when_required(sample_tracks, base_user):
    cfg = {"enabled": True, "require_track_match": True}
    u = dict(base_user)
    u["active_tracks"] = ["product_management"]
    ok, reason, _ = evaluate_title_fit(
        "Registered Nurse",
        "",
        title_fit_cfg=cfg,
        user=u,
        all_tracks=sample_tracks,
    )
    assert not ok
    assert "no matching track" in reason


def test_sniffer_helpers_return_strings():
    from apps.cli.legacy.core.title_fit_gate import (
        sniffer_constraints_paragraph,
        sniffer_role_bullet_text,
    )

    assert "Product" in sniffer_role_bullet_text() or "product" in sniffer_role_bullet_text().lower()
    assert "YOE" in sniffer_constraints_paragraph() or "yoe" in sniffer_constraints_paragraph().lower()
