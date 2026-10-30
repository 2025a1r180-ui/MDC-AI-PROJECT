"""
Database abstraction layer for Echo Journal.
Handles SQLite connection pools for development/testing, and supports PostgreSQL for production.
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional

DEFAULT_DB_PATH = os.environ.get("DATABASE_PATH", "echo_journal.db")


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Open and configure a database connection.
    Enforces foreign keys, WAL mode, and returns sqlite3.Row for dictionary-like access.
    """
    path = db_path or os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)
    
    # In-memory database check for tests
    is_memory = path == ":memory:"
    if not is_memory:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    # Enforce foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON;")
    if not is_memory:
        conn.execute("PRAGMA journal_mode = WAL;")
        
    return conn


def get_db() -> sqlite3.Connection:
    """Return the request-scoped database connection used by Flask routes."""
    from flask import current_app, g

    if "db_conn" not in g:
        g.db_conn = get_db_connection(current_app.config.get("DATABASE_PATH"))
    return g.db_conn


def init_db(conn: sqlite3.Connection):
    """Initialize schema tables with indexes and full-text search."""
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        opt_in_external_ai INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Journal entries table - with user_id foreign key and cascade delete
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        mood TEXT,
        tags TEXT DEFAULT '',
        word_count INTEGER DEFAULT 0,
        reading_time_minutes INTEGER DEFAULT 1,
        analysis_status TEXT DEFAULT 'pending',
        primary_emotion TEXT,
        emotion_scores TEXT,
        sentiment_label TEXT,
        sentiment_score REAL,
        model_name TEXT,
        model_version TEXT,
        analyzed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)
    
    # Indexes for account isolation and performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entries_user_id ON entries (user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entries_user_created ON entries (user_id, created_at DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entries_user_mood ON entries (user_id, mood);")
    
    # Full-text search (FTS5) for keyword retrieval
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
        title,
        content,
        tags,
        content='entries',
        content_rowid='id'
    );
    """)
    
    # Triggers to keep FTS index synced
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
      INSERT INTO entries_fts(rowid, title, content, tags) VALUES (new.id, new.title, new.content, new.tags);
    END;
    """)
    
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
      INSERT INTO entries_fts(entries_fts, rowid, title, content, tags) VALUES('delete', old.id, old.title, old.content, old.tags);
    END;
    """)
    
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
      INSERT INTO entries_fts(entries_fts, rowid, title, content, tags) VALUES('delete', old.id, old.title, old.content, old.tags);
      INSERT INTO entries_fts(rowid, title, content, tags) VALUES (new.id, new.title, new.content, new.tags);
    END;
    """)
    
    conn.commit()
