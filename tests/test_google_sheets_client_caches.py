"""GoogleSheetsClient URL cache invalidation and run_pipeline Sheets gate helpers."""

from apps.cli.legacy.core.google_sheets_client import GoogleSheetsClient, SheetsReadError
from apps.cli.run_pipeline import _is_sheets_read_failure


def test_invalidate_sheet_url_caches_clears_all():
    c = GoogleSheetsClient.__new__(GoogleSheetsClient)  # bypass connect / credentials
    c._cached_existing_urls = {"a"}
    c._cached_applied_urls = {"b"}
    c._cached_evaluated_or_applied_urls = {"c"}
    c._worksheet_header_row_cache = {}
    GoogleSheetsClient.invalidate_sheet_url_caches(c)
    assert c._cached_existing_urls is None
    assert c._cached_applied_urls is None
    assert c._cached_evaluated_or_applied_urls is None


def test_is_sheets_read_failure_sheets_read_error():
    assert _is_sheets_read_failure(SheetsReadError("quota"))


def test_with_retries_paces_when_env_set(monkeypatch):
    monkeypatch.setenv("SHEETS_MIN_REQUEST_INTERVAL_SEC", "0.2")
    sleeps: list[float] = []
    monkeypatch.setattr("apps.cli.legacy.core.google_sheets_client.time.sleep", lambda s: sleeps.append(float(s)))
    c = GoogleSheetsClient.__new__(GoogleSheetsClient)
    c._last_sheets_call_end_monotonic = 0.0

    def noop():
        return 1

    assert c._with_retries(noop, op_name="t1") == 1
    assert c._with_retries(noop, op_name="t2") == 1
    assert len(sleeps) >= 1
    assert any(s >= 0.15 for s in sleeps)


def test_with_retries_respects_sheets_retry_max(monkeypatch):
    monkeypatch.setenv("SHEETS_RETRY_MAX", "2")
    monkeypatch.setenv("SHEETS_MIN_REQUEST_INTERVAL_SEC", "0")
    monkeypatch.setattr("apps.cli.legacy.core.google_sheets_client.time.sleep", lambda s: None)
    c = GoogleSheetsClient.__new__(GoogleSheetsClient)
    c._last_sheets_call_end_monotonic = 0.0
    n = {"i": 0}

    def flaky():
        n["i"] += 1
        if n["i"] < 2:
            raise RuntimeError("APIError: [429]: Quota exceeded for quota metric 'Read requests'")
        return "ok"

    out = c._with_retries(flaky, op_name="flaky")
    assert out == "ok"
    assert n["i"] == 2


def test_is_sheets_read_failure_429_message():
    assert _is_sheets_read_failure(RuntimeError("APIError: [429]: Quota exceeded"))
