"""
Repository layer for Echo Journal.
Enforces NON-NEGOTIABLE RULE 4: Strict Account Isolation.
Every database query touching journal data is strictly parameterized with the
authenticated user's ID.
"""

import json
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime


class UserRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create_user(self, username: str, email: str, password_hash: str, role: str = "user") -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, role, opt_in_external_ai)
            VALUES (?, ?, ?, ?, 0)
            """,
            (username.strip(), email.strip().lower(), password_hash, role)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_by_id(self, user_id: int) -> Optional[sqlite3.Row]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()

    def get_by_email(self, email: str) -> Optional[sqlite3.Row]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
        return cursor.fetchone()

    def get_by_username(self, username: str) -> Optional[sqlite3.Row]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username.strip(),))
        return cursor.fetchone()

    def update_ai_opt_in(self, user_id: int, opt_in: bool) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE users SET opt_in_external_ai = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (1 if opt_in else 0, user_id)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_account(self, user_id: int) -> bool:
        """Completely delete user and cascade all associated journal entries."""
        cursor = self.conn.cursor()
        # Explicit delete on entries first to be safe across all DB engines
        cursor.execute("DELETE FROM entries WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()
        return cursor.rowcount > 0


class JournalRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def _calc_metrics(self, content: str) -> tuple[int, int]:
        words = len(content.split())
        reading_time = max(1, round(words / 200))
        return words, reading_time

    def create_entry(
        self,
        user_id: int,
        title: str,
        content: str,
        mood: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        words, reading_time = self._calc_metrics(content)
        tags_str = ",".join(sorted(set(t.strip().lower() for t in tags))) if tags else ""
        
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO entries (user_id, title, content, mood, tags, word_count, reading_time_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, title.strip(), content.strip(), mood.strip().lower() if mood else None, tags_str, words, reading_time)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_entry(self, entry_id: int, user_id: int) -> Optional[sqlite3.Row]:
        """
        Retrieve entry ONLY IF it belongs to the authenticated user.
        Never query by entry_id alone.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM entries WHERE id = ? AND user_id = ?",
            (entry_id, user_id)
        )
        return cursor.fetchone()

    def get_user_entries(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
        mood: Optional[str] = None,
        tag: Optional[str] = None
    ) -> List[sqlite3.Row]:
        """Retrieve entries strictly belonging to user_id, with optional mood and tag filters."""
        cursor = self.conn.cursor()
        query = "SELECT * FROM entries WHERE user_id = ?"
        params: List[Any] = [user_id]
        
        if mood:
            query += " AND mood = ?"
            params.append(mood.strip().lower())
            
        if tag:
            # Tag match in comma-separated list
            query += " AND (tags = ? OR tags LIKE ? OR tags LIKE ? OR tags LIKE ?)"
            clean_tag = tag.strip().lower()
            params.extend([clean_tag, f"{clean_tag},%", f"%,{clean_tag}", f"%,{clean_tag},%"])
            
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        return cursor.fetchall()

    def update_entry(
        self,
        entry_id: int,
        user_id: int,
        title: str,
        content: str,
        mood: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Update entry ONLY IF it belongs to user_id."""
        words, reading_time = self._calc_metrics(content)
        tags_str = ",".join(sorted(set(t.strip().lower() for t in tags))) if tags else ""
        
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE entries
            SET title = ?, content = ?, mood = ?, tags = ?, word_count = ?, reading_time_minutes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (title.strip(), content.strip(), mood.strip().lower() if mood else None, tags_str, words, reading_time, entry_id, user_id)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def save_entry_analysis(
        self,
        entry_id: int,
        user_id: int,
        analysis_data: Dict[str, Any]
    ) -> bool:
        """Store emotion & sentiment analysis metadata strictly filtered by user_id."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE entries
            SET analysis_status = ?,
                primary_emotion = ?,
                emotion_scores = ?,
                sentiment_label = ?,
                sentiment_score = ?,
                model_name = ?,
                model_version = ?,
                analyzed_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (
                analysis_data.get("status", "completed"),
                analysis_data.get("primary_emotion"),
                json.dumps(analysis_data.get("emotion_scores", {})),
                analysis_data.get("sentiment_label"),
                analysis_data.get("sentiment_score"),
                analysis_data.get("model_name"),
                analysis_data.get("model_version"),
                entry_id,
                user_id
            )
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_entry(self, entry_id: int, user_id: int) -> bool:
        """Delete entry ONLY IF it belongs to user_id."""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM entries WHERE id = ? AND user_id = ?",
            (entry_id, user_id)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def search_entries(self, user_id: int, search_term: str, limit: int = 50) -> List[sqlite3.Row]:
        """
        Search entries by keyword using LIKE and FTS with strict user_id boundary.
        """
        cursor = self.conn.cursor()
        clean_term = search_term.strip()
        if not clean_term:
            return self.get_user_entries(user_id, limit=limit)
            
        pattern = f"%{clean_term}%"
        cursor.execute(
            """
            SELECT * FROM entries
            WHERE user_id = ? AND (title LIKE ? OR content LIKE ? OR tags LIKE ?)
            ORDER BY created_at DESC LIMIT ?
            """,
            (user_id, pattern, pattern, pattern, limit)
        )
        return cursor.fetchall()

    def export_entries_json(self, user_id: int) -> str:
        """Export all entries for the user as formatted JSON."""
        entries = self.get_user_entries(user_id, limit=10000)
        data = []
        for e in entries:
            data.append({
                "id": e["id"],
                "title": e["title"],
                "content": e["content"],
                "mood": e["mood"],
                "tags": [t for t in (e["tags"] or "").split(",") if t],
                "word_count": e["word_count"],
                "reading_time_minutes": e["reading_time_minutes"],
                "created_at": e["created_at"],
                "updated_at": e["updated_at"]
            })
        return json.dumps({"user_id": user_id, "total_entries": len(data), "entries": data}, indent=2)

    def export_entries_markdown(self, user_id: int) -> str:
        """Export all entries for the user as formatted Markdown."""
        entries = self.get_user_entries(user_id, limit=10000)
        md_lines = [
            f"# Echo Journal Export",
            f"Exported on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Total Entries: {len(entries)}",
            "",
            "---",
            ""
        ]
        
        for e in entries:
            tags_display = " ".join(f"#{t}" for t in (e["tags"] or "").split(",") if t)
            md_lines.extend([
                f"## {e['title']}",
                f"**Date:** {e['created_at']}  ",
                f"**Mood:** {e['mood'] or 'Unspecified'}  ",
                f"**Tags:** {tags_display if tags_display else 'None'}  ",
                f"**Length:** {e['word_count']} words  ",
                "",
                e["content"],
                "",
                "---",
                ""
            ])
            
        return "\n".join(md_lines)

    def get_entry_count(self, user_id: int) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM entries WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row["count"] if row else 0
