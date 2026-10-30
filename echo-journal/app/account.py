"""
Account Blueprint for Echo Journal.
Handles user profile settings, external AI opt-in consent toggle, and complete account deletion with cascade.
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    current_app
)
from .auth import login_required
from .db import get_db_connection
from .repository import UserRepository, JournalRepository
from .security import verify_password

account_bp = Blueprint("account", __name__)


@account_bp.route("/", methods=["GET"])
@login_required
def index():
    user_id = session["user_id"]
    conn = get_db_connection(current_app.config.get("DATABASE_PATH"))
    user_repo = UserRepository(conn)
    journal_repo = JournalRepository(conn)

    user = user_repo.get_by_id(user_id)
    entry_count = journal_repo.get_entry_count(user_id)
    conn.close()

    return render_template(
        "account/index.html",
        user=user,
        entry_count=entry_count
    )


@account_bp.route("/opt-in", methods=["POST"])
@login_required
def toggle_opt_in():
    user_id = session["user_id"]
    opt_in = request.form.get("opt_in") == "true"

    conn = get_db_connection(current_app.config.get("DATABASE_PATH"))
    repo = UserRepository(conn)
    repo.update_ai_opt_in(user_id=user_id, opt_in=opt_in)
    conn.close()

    if opt_in:
        flash("External AI consent granted. You can revoke this anytime.", "info")
    else:
        flash("External AI consent revoked. All processing remains strictly local.", "info")

    return redirect(url_for("account.index"))


@account_bp.route("/delete", methods=["POST"])
@login_required
def delete_account():
    user_id = session["user_id"]
    confirm_password = request.form.get("confirm_password", "")

    conn = get_db_connection(current_app.config.get("DATABASE_PATH"))
    user_repo = UserRepository(conn)
    user = user_repo.get_by_id(user_id)

    if not user or not verify_password(confirm_password, user["password_hash"]):
        conn.close()
        flash("Incorrect password. Account deletion aborted.", "error")
        return redirect(url_for("account.index"))

    user_repo.delete_account(user_id)
    conn.close()

    session.clear()
    flash("Your account and all associated journal entries have been completely erased.", "info")
    return redirect(url_for("auth.register"))
