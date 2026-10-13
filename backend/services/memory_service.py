"""Bounded, user-scoped conversation memory stored in SQLite."""

import json
from datetime import datetime, timedelta, timezone

from backend.services.config import bounded_setting
from database.database import database_connection


def get_conversation_history(user_id):
    maximum = _message_limit()
    retention_days = bounded_setting("SPENDWISE_MEMORY_RETENTION_DAYS", 30, 1, 365)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    with database_connection() as connection:
        connection.execute(
            "DELETE FROM assistant_messages WHERE user_id = ? AND created_at < ?",
            (user_id, cutoff),
        )
        rows = connection.execute(
            "SELECT role, content FROM assistant_messages WHERE user_id = ? "
            "AND created_at >= ? ORDER BY id DESC LIMIT ?",
            (user_id, cutoff, maximum),
        ).fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]


def save_conversation_turn(user_id, user_message, assistant_message, connection=None):
    maximum = _message_limit()
    retention_days = bounded_setting("SPENDWISE_MEMORY_RETENTION_DAYS", 30, 1, 365)
    now = datetime.now(timezone.utc).isoformat()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
    if connection is None:
        with database_connection() as active_connection:
            _store_turn(active_connection, user_id, user_message, assistant_message, cutoff, now, maximum)
    else:
        _store_turn(connection, user_id, user_message, assistant_message, cutoff, now, maximum)


def _store_turn(connection, user_id, user_message, assistant_message, cutoff, now, maximum):
    connection.execute(
        "DELETE FROM assistant_messages WHERE user_id = ? AND created_at < ?",
        (user_id, cutoff),
    )
    connection.executemany(
        "INSERT INTO assistant_messages (user_id, role, content, created_at) "
        "VALUES (?, ?, ?, ?)",
        [
            (user_id, "user", user_message[:1000], now),
            (user_id, "assistant", assistant_message[:4000], now),
        ],
    )
    connection.execute(
        "DELETE FROM assistant_messages WHERE user_id = ? AND id NOT IN "
        "(SELECT id FROM assistant_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?)",
        (user_id, user_id, maximum),
    )


def _message_limit():
    maximum = bounded_setting("SPENDWISE_MEMORY_MAX_MESSAGES", 10, 2, 20)
    return max(2, maximum - maximum % 2)


def get_conversation_focus(user_id):
    with database_connection() as connection:
        row = connection.execute(
            "SELECT focus_json FROM assistant_memory_focus WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if row is None:
        return None
    try:
        focus = json.loads(row["focus_json"])
    except json.JSONDecodeError:
        return None
    return focus if isinstance(focus, dict) else None


def save_conversation_focus(user_id, focus):
    payload = json.dumps(
        {
            "tool": focus.get("tool"),
            "arguments": focus.get("arguments") or {},
            "category": focus.get("category"),
            "top_category": focus.get("top_category"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    now = datetime.now(timezone.utc).isoformat()
    with database_connection() as connection:
        connection.execute(
            "INSERT INTO assistant_memory_focus (user_id, focus_json, updated_at) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET "
            "focus_json = excluded.focus_json, updated_at = excluded.updated_at",
            (user_id, payload, now),
        )
