"""OpenRouter path on LLMRouter (mocked HTTP via _chat_completions)."""

import json
import os
from unittest.mock import patch

from apps.cli.legacy.core.llm_router import LLMRouter


def _or_cfg(**overrides):
    base = {
        "provider": "openrouter",
        "openrouter_model": "primary/model",
        "openrouter_fallback_model": "fallback/model",
        "fallback_provider": "openrouter_fallback",
        "openrouter_fast_fallback": False,
        "openrouter_site_url": "https://ref.example",
        "openrouter_app_name": "UnitTest",
    }
    base.update(overrides)
    return base


@patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test"}, clear=False)
@patch("apps.cli.legacy.core.llm_router.get_evaluation_config")
def test_openrouter_primary_success(mock_eval):
    mock_eval.return_value = _or_cfg()
    router = LLMRouter()
    ok_json = json.dumps({"ok": True})
    with patch.object(router, "_chat_completions", return_value=ok_json) as m:
        text, eng = router.generate_content("system", "user")
    assert text == ok_json
    assert eng == "OPENROUTER"
    m.assert_called_once()
    kw = m.call_args.kwargs
    assert kw["model"] == "primary/model"
    assert kw["base_url"] == "https://openrouter.ai/api/v1"
    assert kw["extra_headers"]["HTTP-Referer"] == "https://ref.example"
    assert kw["extra_headers"]["X-Title"] == "UnitTest"
    assert kw["fast_429_handoff"] is False


@patch.dict(
    os.environ,
    {"OPENROUTER_API_KEY": "sk-or-test", "OPENROUTER_BASE_URL": "https://custom.example/v1"},
    clear=False,
)
@patch("apps.cli.legacy.core.llm_router.get_evaluation_config")
def test_openrouter_respects_base_url_env(mock_eval):
    mock_eval.return_value = _or_cfg()
    router = LLMRouter()
    with patch.object(router, "_chat_completions", return_value="ok") as m:
        router.generate_content("s", "u")
    assert m.call_args.kwargs["base_url"] == "https://custom.example/v1"


@patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test"}, clear=False)
@patch("apps.cli.legacy.core.llm_router.get_evaluation_config")
def test_openrouter_fallback_when_primary_empty(mock_eval):
    mock_eval.return_value = _or_cfg()
    router = LLMRouter()
    fb = json.dumps({"fallback": True})
    with patch.object(router, "_chat_completions", side_effect=["", fb]) as m:
        text, eng = router.generate_content("s", "u")
    assert text == fb
    assert eng == "OPENROUTER_FALLBACK"
    assert m.call_count == 2
    assert m.call_args_list[0].kwargs["model"] == "primary/model"
    assert m.call_args_list[1].kwargs["model"] == "fallback/model"


@patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test"}, clear=False)
@patch("apps.cli.legacy.core.llm_router.get_evaluation_config")
def test_openrouter_no_fallback_when_fallback_provider_none(mock_eval):
    mock_eval.return_value = _or_cfg(fallback_provider="none")
    router = LLMRouter()
    with patch.object(router, "_chat_completions", return_value="") as m:
        text, eng = router.generate_content("s", "u")
    assert eng == "FAILED"
    m.assert_called_once()


@patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-or-test"}, clear=False)
@patch("apps.cli.legacy.core.llm_router.get_evaluation_config")
def test_openrouter_override_model_kwarg(mock_eval):
    mock_eval.return_value = _or_cfg()
    router = LLMRouter()
    with patch.object(router, "_chat_completions", return_value="x") as m:
        router.generate_content("s", "u", model="override/model")
    assert m.call_args.kwargs["model"] == "override/model"


@patch("apps.cli.legacy.core.llm_router.get_evaluation_config")
@patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False)
def test_openrouter_missing_key_fails(_mock_eval):
    _mock_eval.return_value = _or_cfg()
    router = LLMRouter()
    text, eng = router.generate_content("s", "u")
    assert eng == "FAILED"
    assert text == ""
