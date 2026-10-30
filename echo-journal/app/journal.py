"""
Journal Blueprint for Echo Journal.
Handles entry creation, listing, reading, editing, deletion, search, and export (JSON/Markdown).
Strictly enforces account isolation across all endpoints.
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    Response,
    abort,
    current_app
)
from .auth import login_required
from .db import get_db_connection
from .repository import JournalRepository
from .validation import validate_entry
from .security import sanitize_text

journal_bp = Blueprint("journal", __name__, url_prefix="/journal")


@journal_bp.route("/")
@login_required
def index():
    user_id = session["user_id"]
    mood = request.args.get("mood")
    tag = request.args.get("tag")
    search_q = request.args.get("q")

    conn = get_db_connection(current_app.config.get("DATABASE_PATH"))
    repo = JournalRepository(conn)

    if search_q:
        entries = repo.search_entries(user_id=user_id, search_term=search_q)
    else:
        entries = repo.get_user_entries(user_id=user_id, mood=mood, tag=tag)

    total_count = repo.get_entry_count(user_id=user_id)
    conn.close()

    return render_template(
        "journal/index.html",
        entries=entries,
        selected_mood=mood,
        selected_tag=tag,
        search_query=search_q,
        total_count=total_count
    )


@journal_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        title = request.form.get("title", "")
        content = request.form.get("content", "")
        mood = request.form.get("mood", "")
        raw_tags = request.form.get("tags", "")

        tags = [t.strip().lower() for t in raw_tags.split(",") if t.strip()]
        is_valid, error_msg = validate_entry(title=title, content=content, mood=mood, tags=tags)
        
        if not is_valid:
            flash(error_msg, "error")
            return render_template(
                "journal/create.html",
                title=title,
                content=content,
                mood=mood,
                tags=raw_tags
            )

        user_id = session["user_id"]
        conn = get_db_connection(current_app.config.get("DATABASE_PATH"))
        repo = JournalRepository(conn)
        entry_id = repo.create_entry(
            user_id=user_id,
            title=title,
            content=content,
            mood=mood if mood else None,
            tags=tags
        )
        conn.close()

        flash("Journal entry recorded quietly.", "success")
        return redirect(url_for("journal.view", entry_id=entry_id))

    return render_template("journal/create.html")


@journal_bp.route("/<int:entry_id>")
@login_required
def view(entry_id: int):
    user_id = session["user_id"]
    conn = get_db_connection(current_app.config.get("DATABASE_PATH"))
    repo = JournalRepository(conn)
    entry = repo.get_entry(entry_id=entry_id, user_id=user_id)
    conn.close()

    if entry is None:
        # Prevent ID enumeration; return 404
        abort(404, description="Journal entry not found or unauthorized.")

    return render_template("journal/view.html", entry=entry)


@journal_bp.route("/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def edit(entry_id: int):
    user_id = session["user_id"]
    conn = get_db_connection(current_app.config.get("DATABASE_PATH"))
    repo = JournalRepository(conn)
    entry = repo.get_entry(entry_id=entry_id, user_id=user_id)

    if entry is None:
        conn.close()
        abort(404, description="Journal entry not found or unauthorized.")

    if request.method == "POST":
        title = request.form.get("title", "")
        content = request.form.get("content", "")
        mood = request.form.get("mood", "")
        raw_tags = request.form.get("tags", "")

        tags = [t.strip().lower() for t in raw_tags.split(",") if t.strip()]
        is_valid, error_msg = validate_entry(title=title, content=content, mood=mood, tags=tags)
        
        if not is_valid:
            flash(error_msg, "error")
            conn.close()
            return render_template(
                "journal/edit.html",
                entry=entry,
                title=title,
                content=content,
                mood=mood,
                tags=raw_tags
            )

        repo.update_entry(
            entry_id=entry_id,
            user_id=user_id,
            title=title,
            content=content,
            mood=mood if mood else None,
            tags=tags
        )
        conn.close()

        flash("Journal entry updated.", "success")
        return redirect(url_for("journal.view", entry_id=entry_id))

    conn.close()
    return render_template("journal/edit.html", entry=entry)


@journal_bp.route("/<int:entry_id>/analyze", methods=["POST"])
@login_required
def analyze(entry_id: int):
    user_id = session["user_id"]
    conn = get_db_connection(current_app.config.get("DATABASE_PATH"))
    repo = JournalRepository(conn)
    entry = repo.get_entry(entry_id=entry_id, user_id=user_id)

    if entry is None:
        conn.close()
        abort(404, description="Journal entry not found or unauthorized.")

    from .ai_analysis import analyze_reflection
    include_compare = request.form.get("compare") == "true"
    result = analyze_reflection(entry["content"], include_comparison=include_compare)

    repo.save_entry_analysis(
        entry_id=entry_id,
        user_id=user_id,
        analysis_data=result.to_dict()
    )
    conn.close()

    if request.headers.get("Accept") == "application/json":
        from flask import jsonify
        return jsonify(result.to_dict())

    flash("Reflection analyzed with custom BiLSTM model. Results recorded with uncertainty notice.", "info")
    return redirect(url_for("journal.view", entry_id=entry_id, compare="1" if include_compare else None))


@journal_bp.route("/<int:entry_id>/delete", methods=["POST"])
@login_required
def delete(entry_id: int):
    user_id = session["user_id"]
    conn = get_db_connection(current_app.config.get("DATABASE_PATH"))
    repo = JournalRepository(conn)
    success = repo.delete_entry(entry_id=entry_id, user_id=user_id)
    conn.close()

    if not success:
        abort(404, description="Journal entry not found or unauthorized.")

    flash("Journal entry deleted.", "info")
    return redirect(url_for("journal.index"))


@journal_bp.route("/export/json")
@login_required
def export_json():
    user_id = session["user_id"]
    conn = get_db_connection(current_app.config.get("DATABASE_PATH"))
    repo = JournalRepository(conn)
    json_data = repo.export_entries_json(user_id=user_id)
    conn.close()

    return Response(
        json_data,
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=echo_journal_export.json"}
    )


@journal_bp.route("/export/markdown")
@login_required
def export_markdown():
    user_id = session["user_id"]
    conn = get_db_connection(current_app.config.get("DATABASE_PATH"))
    repo = JournalRepository(conn)
    md_data = repo.export_entries_markdown(user_id=user_id)
    conn.close()

    return Response(
        md_data,
        mimetype="text/markdown",
        headers={"Content-Disposition": "attachment; filename=echo_journal_export.md"}
    )
