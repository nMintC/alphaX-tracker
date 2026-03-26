"""
Database query helpers for the follow tracker.
"""

import sqlite3
from contextlib import contextmanager

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ── Smart Accounts ────────────────────────────────────────────────────

def get_active_accounts():
    """Get all active smart accounts to monitor."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM smart_accounts WHERE is_active = 1 ORDER BY tag, username"
        ).fetchall()
        return [dict(r) for r in rows]


def add_account(username: str, tag: str = "other"):
    """Add a smart account to track."""
    username = username.lower().strip().lstrip("@")
    with get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO smart_accounts (username, tag) VALUES (?, ?)",
                (username, tag),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # already exists


def remove_account(username: str):
    """Remove (deactivate) a smart account."""
    username = username.lower().strip().lstrip("@")
    with get_db() as conn:
        conn.execute(
            "UPDATE smart_accounts SET is_active = 0 WHERE username = ?",
            (username,),
        )
        conn.commit()


# ── Following Snapshot ────────────────────────────────────────────────

def get_snapshot(account_id: int) -> set:
    """Get the current snapshot of who this smart account follows."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT following_username FROM following_snapshot WHERE smart_account_id = ?",
            (account_id,),
        ).fetchall()
        return {row["following_username"] for row in rows}


def add_to_snapshot(account_id: int, usernames: list):
    """Add new usernames to the snapshot."""
    with get_db() as conn:
        for uname in usernames:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO following_snapshot (smart_account_id, following_username) VALUES (?, ?)",
                    (account_id, uname.lower()),
                )
            except sqlite3.IntegrityError:
                pass
        conn.commit()


def is_first_run(account_id: int) -> bool:
    """Check if this is the first time we're fetching for this account."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM following_snapshot WHERE smart_account_id = ?",
            (account_id,),
        ).fetchone()
        return row["cnt"] == 0


# ── Follow Events (history) ──────────────────────────────────────────

def record_follow_event(
    smart_username: str,
    smart_tag: str,
    followed_username: str,
    followed_name: str = "",
    followed_bio: str = "",
    followed_followers: int = 0,
    followed_avatar_url: str = "",
    followed_verified: bool = False,
):
    """Record a detected new follow event."""
    with get_db() as conn:
        conn.execute(
            """INSERT INTO follow_events
               (smart_username, smart_tag, followed_username, followed_name,
                followed_bio, followed_followers, followed_avatar_url, followed_verified)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                smart_username, smart_tag, followed_username, followed_name,
                followed_bio, followed_followers, followed_avatar_url, followed_verified,
            ),
        )
        conn.commit()


def get_recent_events(limit: int = 20):
    """Get most recent follow events."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM follow_events ORDER BY detected_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
