"""Persist jobs to disk when Sheets append fails."""
import json
from unittest.mock import MagicMock

import pytest
import requests
from gspread.exceptions import APIError

import apps.cli.legacy.core.google_sheets_client as gsc


def test_add_jobs_persists_fallback_on_append_failure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SHEET_APPEND_FALLBACK_DIR", str(tmp_path / "fb"))
    monkeypatch.setattr(gsc, "get_worksheet_tab_date", lambda: "2026-04-01")

    client = gsc.GoogleSheetsClient()
    client.sheet = MagicMock()
    client.get_existing_urls = MagicMock(return_value=set())
    client.get_applied_urls = MagicMock(return_value=set())
    client._with_retries = MagicMock(side_effect=RuntimeError("quota"))
    client._load_jd_cache = MagicMock(return_value={})
    client._save_jd_cache = MagicMock()

    jobs = [
        {
            "url": "https://example.com/job/1",
            "title": "PM",
            "company": "Acme",
            "location": "Remote",
            "description": "full jd text here",
            "jd_verified": True,
            "jd_fetch_method": "m",
            "jd_fetch_reason": "r",
        }
    ]
    with pytest.raises(RuntimeError, match="quota"):
        client.add_jobs(jobs)

    fb_dir = tmp_path / "fb"
    files = list(fb_dir.glob("failed_*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert data["tab_date"] == "2026-04-01"
    assert len(data["jobs"]) == 1
    assert data["jobs"][0]["url"] == "https://example.com/job/1"
    client._save_jd_cache.assert_called_once()


def test_jd_cache_saved_before_append(tmp_path, monkeypatch):
    """JD cache must be updated before append_rows so JD survives append failure."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SHEET_APPEND_FALLBACK_DIR", str(tmp_path / "fb"))

    calls: list[str] = []

    def track_with_retries(fn, op_name=None, retries=None, base_sleep=None, **_kw):
        if op_name == "append_rows":
            calls.append("append")
        return fn()

    tmp = MagicMock()

    class Client(gsc.GoogleSheetsClient):
        def __init__(self):
            super().__init__()
            self.sheet = tmp
            self.get_existing_urls = MagicMock(return_value=set())
            self.get_applied_urls = MagicMock(return_value=set())

        def _with_retries(self, fn, op_name="operation", retries=None, base_sleep=None):
            return track_with_retries(fn, op_name=op_name, retries=retries, base_sleep=base_sleep)

    monkeypatch.setattr(gsc, "get_worksheet_tab_date", lambda: "2026-04-10")
    c = Client()
    c._load_jd_cache = MagicMock(return_value={})
    save = MagicMock()
    c._save_jd_cache = save

    resp = requests.Response()
    resp.status_code = 429

    def boom(*_args, **_kwargs):
        raise APIError(resp)

    tmp.append_rows = boom

    jobs = [
        {
            "url": "https://example.com/job/2",
            "title": "BA",
            "company": "Co",
            "location": "US",
            "description": "jd",
            "jd_verified": True,
        }
    ]
    with pytest.raises(APIError):
        c.add_jobs(jobs)

    assert calls == ["append"]
    save.assert_called_once()
