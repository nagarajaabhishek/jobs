"""
SQLite outbox for failed Google Sheets writes (append jobs, evaluation row updates).

Stdlib sqlite3 only. WAL mode. See scripts/tools/sync_sheet_outbox.py for replay.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any

from apps.cli.legacy.core.config import get_local_store_config

SCHEMA = """
CREATE TABLE IF NOT EXISTS sheet_outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    op_type TEXT NOT NULL,
    tab_date TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    error_text TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_attempt_at TEXT,
    last_error TEXT
);
CREATE INDEX IF NOT EXISTS idx_sheet_outbox_status_created
ON sheet_outbox (status, created_at);
"""


def is_sheet_outbox_enabled() -> bool:
    """True when outbox writes should be attempted."""
    if os.environ.get("PIPELINE_OUTBOX_DB", "").strip():
        return True
    if os.environ.get("LOCAL_STORE_ENABLED", "").strip().lower() in ("1", "true", "yes"):
        return True
    cfg = get_local_store_config()
    return bool(cfg.get("enabled", False))


def resolve_outbox_db_path() -> str:
    """Absolute path to the outbox database file."""
    env = os.environ.get("PIPELINE_OUTBOX_DB", "").strip()
    if env:
        p = env
    else:
        cfg = get_local_store_config()
        p = str(cfg.get("db_path") or "data/pipeline_outbox.db").strip() or "data/pipeline_outbox.db"
    if os.path.isabs(p):
        return p
    return os.path.abspath(os.path.join(os.getcwd(), p))


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def _connect(path: str | None = None) -> sqlite3.Connection:
    db_path = path or resolve_outbox_db_path()
    _ensure_parent_dir(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    init_schema(conn)
    return conn


def enqueue_outbox(
    op_type: str,
    tab_date: str,
    payload: dict[str, Any],
    error: str,
    db_path: str | None = None,
) -> int | None:
    """
    Insert one replayable batch. Returns row id, or None if outbox disabled / insert failed.
    Does not raise on insert failure (logs and returns None).
    """
    if not is_sheet_outbox_enabled():
        return None
    if op_type not in ("add_jobs", "update_eval"):
        raise ValueError(f"Invalid op_type: {op_type}")
    path = db_path or resolve_outbox_db_path()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    err_trunc = (error or "")[:4000]
    try:
        conn = _connect(path)
        try:
            cur = conn.execute(
                """
                INSERT INTO sheet_outbox (op_type, tab_date, payload_json, error_text, status, created_at)
                VALUES (?, ?, ?, ?, 'pending', ?)
                """,
                (
                    op_type,
                    tab_date[:32],
                    json.dumps(payload, ensure_ascii=False, default=str),
                    err_trunc,
                    now,
                ),
            )
            conn.commit()
            last = cur.lastrowid
            if last is None:
                return None
            rid = int(last)
            print(f"[sheet_outbox] Queued op={op_type} tab={tab_date} id={rid} db={path}")
            return rid
        finally:
            conn.close()
    except Exception as e:
        print(f"[sheet_outbox] Failed to enqueue: {e}")
        return None


def list_pending(limit: int = 100, db_path: str | None = None) -> list[dict[str, Any]]:
    path = db_path or resolve_outbox_db_path()
    if not os.path.isfile(path):
        return []
    conn = sqlite3.connect(path)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, op_type, tab_date, payload_json, error_text, status, created_at, attempts, last_attempt_at, last_error
            FROM sheet_outbox
            WHERE status = 'pending'
            ORDER BY id ASC
            LIMIT ?
            """,
            (max(1, int(limit)),),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def mark_synced(row_id: int, db_path: str | None = None) -> None:
    path = db_path or resolve_outbox_db_path()
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "UPDATE sheet_outbox SET status = 'synced', last_error = NULL WHERE id = ?",
            (row_id,),
        )
        conn.commit()
    finally:
        conn.close()


def mark_dead(row_id: int, err: str, db_path: str | None = None) -> None:
    path = db_path or resolve_outbox_db_path()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            UPDATE sheet_outbox
            SET status = 'dead', last_error = ?, last_attempt_at = ?
            WHERE id = ?
            """,
            ((err or "")[:4000], now, row_id),
        )
        conn.commit()
    finally:
        conn.close()


def bump_attempt(row_id: int, err: str, db_path: str | None = None) -> None:
    path = db_path or resolve_outbox_db_path()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            UPDATE sheet_outbox
            SET attempts = attempts + 1, last_attempt_at = ?, last_error = ?
            WHERE id = ?
            """,
            (now, (err or "")[:4000], row_id),
        )
        conn.commit()
    finally:
        conn.close()
