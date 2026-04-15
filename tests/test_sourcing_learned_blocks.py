"""Tests for sourcing_learned_blocks (title phrase mining + filter)."""
from __future__ import annotations

import os
import sys

import pytest
import yaml

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.cli.legacy.core.sourcing_learned_blocks import (  # noqa: E402
    learned_block_hit,
    load_learned_blocked_phrases_for_filter,
    mine_blocking_phrases,
    title_features,
)


def test_title_features_bigrams():
    f = title_features("Senior Salesforce Product Manager")
    assert "salesforce" in f or any("salesforce" in x for x in f)


def test_mine_prefers_neg_skew():
    neg = [
        "Salesforce Business Analyst",
        "Salesforce Implementation Consultant",
        "Salesforce Admin Lead",
    ]
    pos = [
        "Product Manager",
        "Associate Product Manager",
        "Business Analyst",
    ]
    out = mine_blocking_phrases(neg, pos, min_neg_count=2, min_lift=1.5, max_phrases=20)
    texts = [x["text"] for x in out]
    assert "salesforce" in texts


def test_learned_block_hit_word_boundary():
    assert learned_block_hit("Bartender Product Owner", ["bar"]) is None
    assert learned_block_hit("Foo Bar", ["foo"]) == "foo"


def test_learned_block_hit_phrase():
    assert learned_block_hit("Customer Success Manager", ["customer success"]) == "customer success"


def test_load_learned_respects_apply_flag(tmp_path):
    import apps.cli.legacy.core.sourcing_learned_blocks as slb

    slb._CACHE = None
    p = tmp_path / "lb.yaml"
    p.write_text(
        yaml.dump({"blocked_phrases": [{"text": "salesforce", "negative_hits": 5}]}),
        encoding="utf-8",
    )
    root = str(tmp_path)

    assert (
        load_learned_blocked_phrases_for_filter(
            project_root=root,
            sourcing_cfg={"apply_learned_title_blocks": False, "learned_title_blocks_path": "lb.yaml"},
        )
        == []
    )

    got = load_learned_blocked_phrases_for_filter(
        project_root=root,
        sourcing_cfg={"apply_learned_title_blocks": True, "learned_title_blocks_path": "lb.yaml"},
    )
    assert got == ["salesforce"]
