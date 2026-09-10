"""
SQLite-backed session storage for interview sessions.

Design decision: InterviewState is a Python dict (with nested lists/dicts) --
SQLite can't store that directly, so we JSON-serialize it into a TEXT column.
This keeps the storage layer completely decoupled from LangGraph's state
shape: if the state schema changes later, this file doesn't need to change.

Why SQLite (not Postgres/Redis) for now: it's a single file, built into
Python's standard library (no extra service to run), and is more than
enough for a solo-dev project where sessions just need to survive a
server restart.

Concurrency notes (Day 5, Option C):
- FastAPI's sync routes run in a threadpool, so two requests CAN execute
  at the same time. Two fixes are applied here:
  1. WAL mode + busy_timeout on the SQLite connection, so concurrent
     writes to DIFFERENT sessions don't throw "database is locked" errors.
  2. A per-session_id threading.Lock (see `session_lock()` below), so that
     a single session's read-modify-write sequence (load -> mutate in
     Python -> save) can't be interleaved by two concurrent requests for
     THAT SAME session_id -- which would otherwise silently drop one
     of the two updates (a "lost update" race condition).
"""

import json
import sqlite3
import threading
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "sessions.db"


def _get_connection() -> sqlite3.Connection:
    """Fresh connection per call -- SQLite connections aren't safely
    shared across FastAPI's request-handling threads.

    WAL (Write-Ahead Logging) mode lets readers and writers work without
    blocking each other as much as the default journal mode does.
    busy_timeout tells SQLite to retry for up to 5 seconds instead of
    immediately raising "database is locked" if it hits a brief conflict.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


# ---------- Per-session locking ----------
#
# Guards against the "lost update" race: two concurrent requests for the
# SAME session_id both reading the old state, both mutating it in Python,
# and the second save() silently overwriting the first one's changes.
#
# defaultdict(threading.Lock) means: first time a session_id is seen, a
# new Lock is created for it automatically; after that, the same Lock
# object is reused every time -- so all requests for that session_id
# serialize through the same lock.
_session_locks: dict[str, threading.Lock] = defaultdict(threading.Lock)
_locks_registry_guard = threading.Lock()  # protects _session_locks itself


@contextmanager
def session_lock(session_id: str):
    """
    Usage:
        with session_lock(session_id):
            state = load_session(session_id)
            state = process_answer(state, ...)
            save_session(session_id, state)

    Everything inside the `with` block for a given session_id runs
    one-request-at-a-time, even if two requests arrive at the same instant.
    Different session_ids are NOT blocked by each other -- only requests
    for the SAME session_id wait on each other.
    """
    with _locks_registry_guard:
        lock = _session_locks[session_id]
    with lock:
        yield


def init_db() -> None:
    """Create the sessions table if it doesn't exist yet. Call this once at
    app startup (see main.py)."""
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                state_json TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)
        conn.commit()
    finally:
        conn.close()


def save_session(session_id: str, state: dict) -> None:
    """Insert or update a session's state. Uses UPSERT so the same
    function works for both 'create new session' and 'update existing one'."""
    conn = _get_connection()
    try:
        conn.execute(
            """
            INSERT INTO sessions (session_id, state_json, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(session_id) DO UPDATE SET
                state_json = excluded.state_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (session_id, json.dumps(state)),
        )
        conn.commit()
    finally:
        conn.close()


def load_session(session_id: str) -> Optional[dict]:
    """Returns the deserialized state dict, or None if session_id doesn't exist."""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT state_json FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    return json.loads(row[0])
