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
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "sessions.db"


def _get_connection() -> sqlite3.Connection:
    """Fresh connection per call -- SQLite connections aren't safely
    shared across FastAPI's request-handling threads."""
    return sqlite3.connect(DB_PATH)


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
