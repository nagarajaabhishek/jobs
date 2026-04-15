"""SQLite sheet_outbox for failed Google Sheets writes."""
import json

import pytest

from apps.cli.legacy.core import sheet_outbox


@pytest.fixture
def outbox_db(tmp_path, monkeypatch):
    db = str(tmp_path / "test_outbox.db")
    monkeypatch.setenv("PIPELINE_OUTBOX_DB", db)
    monkeypatch.setenv("LOCAL_STORE_ENABLED", "1")
    yield db


def test_enqueue_list_mark_synced(outbox_db):
    rid = sheet_outbox.enqueue_outbox(
        "add_jobs",
        "2026-04-10",
        {"jobs": [{"url": "https://example.com/a", "title": "T"}]},
        "quota",
        db_path=outbox_db,
    )
    assert rid is not None and rid > 0
    pending = sheet_outbox.list_pending(limit=50, db_path=outbox_db)
    assert len(pending) == 1
    assert pending[0]["op_type"] == "add_jobs"
    payload = json.loads(pending[0]["payload_json"])
    assert len(payload["jobs"]) == 1
    sheet_outbox.mark_synced(rid, db_path=outbox_db)
    assert sheet_outbox.list_pending(limit=50, db_path=outbox_db) == []


def test_mark_dead_and_bump_attempt(outbox_db):
    rid = sheet_outbox.enqueue_outbox(
        "update_eval",
        "2026-04-11",
        {"updates": [{"row_index": 5, "match_type": "X", "score": 80}]},
        "err0",
        db_path=outbox_db,
    )
    assert rid
    sheet_outbox.mark_dead(rid, "give up", db_path=outbox_db)
    pending = sheet_outbox.list_pending(limit=50, db_path=outbox_db)
    assert pending == []

    rid2 = sheet_outbox.enqueue_outbox("add_jobs", "2026-04-12", {"jobs": []}, "e", db_path=outbox_db)
    sheet_outbox.bump_attempt(rid2, "retry fail", db_path=outbox_db)
    conn = __import__("sqlite3").connect(outbox_db)
    try:
        row = conn.execute("SELECT attempts, last_error FROM sheet_outbox WHERE id = ?", (rid2,)).fetchone()
        assert row[0] == 1
        assert "retry fail" in (row[1] or "")
    finally:
        conn.close()


def test_list_pending_empty_missing_file(tmp_path, monkeypatch):
    missing = str(tmp_path / "nope.db")
    monkeypatch.chdir(tmp_path)
    assert sheet_outbox.list_pending(db_path=missing) == []


def test_enqueue_disabled_returns_none(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PIPELINE_OUTBOX_DB", raising=False)
    monkeypatch.delenv("LOCAL_STORE_ENABLED", raising=False)
    # No pipeline.yaml in tmp -> defaults local_store.enabled False
    r = sheet_outbox.enqueue_outbox("add_jobs", "2026-01-01", {"jobs": []}, "x", db_path=str(tmp_path / "x.db"))
    assert r is None
