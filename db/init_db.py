"""
Create the database tables.
Run: python -m db.init_db
"""

import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ── Smart Accounts (who we're monitoring) ─────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS smart_accounts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            tag         TEXT NOT NULL DEFAULT 'other',
            added_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active   BOOLEAN DEFAULT 1
        )
    """)

    # ── Following Snapshot (current following list per smart account) ──
    # We store the set of user IDs each smart account follows.
    # On each poll, we diff to find NEW follows.
    c.execute("""
        CREATE TABLE IF NOT EXISTS following_snapshot (
            smart_account_id    INTEGER NOT NULL,
            following_username  TEXT NOT NULL,
            added_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (smart_account_id) REFERENCES smart_accounts(id),
            UNIQUE(smart_account_id, following_username)
        )
    """)

    # ── Follow Events (history of detected new follows) ───────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS follow_events (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            smart_username      TEXT NOT NULL,
            smart_tag           TEXT,
            followed_username   TEXT NOT NULL,
            followed_name       TEXT,
            followed_bio        TEXT,
            followed_followers  INTEGER DEFAULT 0,
            followed_avatar_url TEXT,
            followed_verified   BOOLEAN DEFAULT 0,
            detected_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_account ON following_snapshot(smart_account_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_events_time ON follow_events(detected_at DESC)")

    conn.commit()
    conn.close()
    print("✅ Database initialized at:", DB_PATH)


if __name__ == "__main__":
    init_db()
