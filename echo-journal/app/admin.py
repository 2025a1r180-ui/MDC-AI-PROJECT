"""
Admin Blueprint for Echo Journal (Milestone 4).

NON-NEGOTIABLE PRIVACY INVARIANT:
- Aggregate metrics ONLY (total users, total entries, entry velocity, emotion distribution).
- ZERO exposure of user entry text, entry titles, or user identifiers.
- Admins have NO backdoor or privilege to read, decrypt, or query individual user journals.
"""

from typing import Dict, Any, List
from collections import Counter, defaultdict
import sqlite3

try:
    from flask import Blueprint, render_template, session, abort, jsonify, request
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

if HAS_FLASK:
    from .auth import login_required
    from .db import get_db
    admin_bp = Blueprint("admin", __name__)
else:
    admin_bp = None


def compute_aggregate_metrics(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Computes system-wide aggregate statistics with mathematical privacy preservation.
    GUARANTEE: The returned dictionary NEVER contains user IDs, entry titles, or entry content.
    """
    cursor = conn.cursor()

    # 1. Total User Count
    cursor.execute("SELECT COUNT(*) as user_count FROM users")
    user_count_row = cursor.fetchone()
    total_users = user_count_row["user_count"] if user_count_row else 0

    # 2. Total Journal Entries
    cursor.execute("SELECT COUNT(*) as entry_count FROM entries")
    entry_count_row = cursor.fetchone()
    total_entries = entry_count_row["entry_count"] if entry_count_row else 0

    # 3. System Velocity (Entries per day over time)
    cursor.execute("""
        SELECT DATE(created_at) as entry_date, COUNT(*) as count
        FROM entries
        GROUP BY DATE(created_at)
        ORDER BY entry_date DESC
        LIMIT 14
    """)
    velocity_rows = cursor.fetchall()
    velocity = [{"date": r["entry_date"], "count": r["count"]} for r in velocity_rows]

    # 4. System Aggregate Emotion Distribution (Without user linkage)
    cursor.execute("""
        SELECT primary_emotion, COUNT(*) as count
        FROM entries
        WHERE primary_emotion IS NOT NULL AND primary_emotion != ''
        GROUP BY primary_emotion
    """)
    emotion_rows = cursor.fetchall()
    emotion_distribution = {r["primary_emotion"]: r["count"] for r in emotion_rows}

    # 5. Average Word Count & Reading Time (Statistical summary only)
    cursor.execute("""
        SELECT AVG(word_count) as avg_words, AVG(reading_time_minutes) as avg_reading_time
        FROM entries
    """)
    avg_row = cursor.fetchone()
    avg_words = round(avg_row["avg_words"] or 0, 1) if avg_row else 0.0
    avg_reading_time = round(avg_row["avg_reading_time"] or 0, 1) if avg_row else 0.0

    # 6. Opt-in External AI Rate
    cursor.execute("SELECT COUNT(*) as opt_in_count FROM users WHERE opt_in_external_ai = 1")
    opt_in_row = cursor.fetchone()
    opt_in_count = opt_in_row["opt_in_count"] if opt_in_row else 0

    return {
        "status": "success",
        "privacy_notice": "AGGREGATE ONLY: Zero user identifiers or journal contents are accessible through this interface.",
        "metrics": {
            "total_users": total_users,
            "total_entries": total_entries,
            "external_ai_opt_in_users": opt_in_count,
            "average_word_count": avg_words,
            "average_reading_time_minutes": avg_reading_time,
            "entry_velocity": velocity,
            "emotion_distribution": emotion_distribution,
        }
    }


if HAS_FLASK:
    @admin_bp.route("/", methods=["GET"])
    @login_required
    def index():
        if session.get("role") != "admin":
            abort(403, description="Access restricted to administrators.")
        
        conn = get_db()
        metrics = compute_aggregate_metrics(conn)
        return render_template("admin/index.html", data=metrics)

    @admin_bp.route("/api/metrics", methods=["GET"])
    @login_required
    def api_metrics():
        if session.get("role") != "admin":
            return jsonify({"error": "Forbidden: Administrator role required"}), 403

        conn = get_db()
        metrics = compute_aggregate_metrics(conn)
        return jsonify(metrics)
