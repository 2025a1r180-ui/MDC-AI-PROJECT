"""
Database Migration Script for Echo Journal (Milestone 6).
Migrates data from local SQLite database (echo_journal.db) to PostgreSQL.

Usage:
    python scripts/migrate_to_postgres.py --sqlite-path echo_journal.db --pg-url postgresql://user:pass@host:5432/dbname
"""

import sys
import argparse
import sqlite3
import json
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Migrate Echo Journal SQLite to PostgreSQL")
    parser.add_argument("--sqlite-path", default="echo_journal.db", help="Path to source SQLite database")
    parser.add_argument("--pg-url", required=False, help="Target PostgreSQL connection string (DATABASE_URL)")
    parser.add_argument("--dry-run", action="store_true", help="Perform extraction and verification without inserting into PostgreSQL")
    return parser.parse_args()

def verify_source(sqlite_path: str):
    if not Path(sqlite_path).exists():
        print(f"Error: Source SQLite database not found at '{sqlite_path}'.")
        return None
    
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM entries")
    entry_count = cursor.fetchone()["count"]
    
    print(f"Verified source SQLite DB: {user_count} users, {entry_count} entries.")
    return conn

def main():
    args = parse_args()
    print("=" * 60)
    print("ECHO JOURNAL — SQLITE TO POSTGRESQL MIGRATION TOOL")
    print("=" * 60)
    
    conn = verify_source(args.sqlite_path)
    if conn is None:
        sys.exit(1)
        
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    cursor.execute("SELECT * FROM entries")
    entries = cursor.fetchall()
    
    print(f"Extracted {len(users)} user rows and {len(entries)} journal entries.")
    
    if args.dry_run or not args.pg_url:
        print("\nDry run completed successfully.")
        print("To execute full migration to a live PostgreSQL database, supply:")
        print("    python scripts/migrate_to_postgres.py --pg-url postgresql://user:pass@host:5432/echo_db")
        conn.close()
        return

    try:
        import psycopg2
    except ImportError:
        print("Notice: 'psycopg2' is required for live PostgreSQL connection.")
        print("Install via: pip install psycopg2-binary")
        conn.close()
        return

    print(f"Connecting to target PostgreSQL instance...")
    pg_conn = psycopg2.connect(args.pg_url)
    pg_cursor = pg_conn.cursor()
    
    # Read schema.sql
    schema_path = Path(__file__).parent / "schema.sql"
    if schema_path.exists():
        pg_cursor.execute(schema_path.read_text())
        print("Applied PostgreSQL DDL schema.")

    # Insert users
    for u in users:
        pg_cursor.execute(
            """
            INSERT INTO users (id, username, email, password_hash, role, opt_in_external_ai, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (u["id"], u["username"], u["email"], u["password_hash"], u["role"], bool(u["opt_in_external_ai"]), u["created_at"], u["updated_at"])
        )
    
    # Insert entries
    for e in entries:
        pg_cursor.execute(
            """
            INSERT INTO entries (
                id, user_id, title, content, mood, tags, word_count, reading_time_minutes,
                analysis_status, primary_emotion, emotion_scores, sentiment_label, sentiment_score,
                model_name, model_version, analyzed_at, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (
                e["id"], e["user_id"], e["title"], e["content"], e["mood"], e["tags"],
                e["word_count"], e["reading_time_minutes"], e["analysis_status"],
                e["primary_emotion"], e["emotion_scores"], e["sentiment_label"],
                e["sentiment_score"], e["model_name"], e["model_version"],
                e["analyzed_at"], e["created_at"], e["updated_at"]
            )
        )
        
    pg_conn.commit()
    pg_conn.close()
    conn.close()
    print("Migration finished successfully! All tables and data populated in PostgreSQL.")

if __name__ == "__main__":
    main()
