"""Database connection and table management for Event Wingman."""

import json
import os
import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional

DB_PATH = os.environ.get("DB_PATH", "event_wingman.db")


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create a SQLite connection with row factory enabled."""
    target_path = db_path or DB_PATH
    conn = sqlite3.connect(target_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextmanager
def get_db(db_path: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite database transactions."""
    target_path = db_path or DB_PATH
    conn = get_db_connection(target_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database tables and indexes."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()

        # People table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS people (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                company TEXT,
                role TEXT,
                topics TEXT DEFAULT '[]',
                notes TEXT DEFAULT '[]',
                first_met_at TEXT NOT NULL,
                last_interaction_at TEXT NOT NULL,
                is_demo INTEGER DEFAULT 0
            );
        """)

        # Companies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            );
        """)

        # Topics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                mention_count INTEGER DEFAULT 1
            );
        """)

        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                person_ids TEXT DEFAULT '[]',
                event_id TEXT DEFAULT 'current_event',
                timestamp TEXT NOT NULL,
                summary TEXT NOT NULL,
                topics TEXT DEFAULT '[]',
                recommendations TEXT DEFAULT '[]',
                ideas TEXT DEFAULT '[]',
                raw_transcript TEXT,
                is_demo INTEGER DEFAULT 0
            );
        """)

        # Ideas table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ideas (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                source_person_id TEXT,
                created_at TEXT NOT NULL,
                is_demo INTEGER DEFAULT 0
            );
        """)

        # Recommendations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                recommended_by_person_id TEXT,
                context TEXT,
                created_at TEXT NOT NULL,
                is_demo INTEGER DEFAULT 0
            );
        """)

        # FollowUps table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS follow_ups (
                id TEXT PRIMARY KEY,
                person_id TEXT NOT NULL,
                action TEXT NOT NULL,
                context TEXT,
                status TEXT DEFAULT 'draft',
                draft_message TEXT,
                created_at TEXT NOT NULL,
                is_demo INTEGER DEFAULT 0
            );
        """)

        # Relationships table for graph modeling
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                source_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                target_type TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                context TEXT,
                created_at TEXT NOT NULL
            );
        """)

        # Indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_people_name ON people(name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_people_company ON people(company);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_followups_person ON follow_ups(person_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_source ON relationships(source_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_target ON relationships(target_id);")


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
