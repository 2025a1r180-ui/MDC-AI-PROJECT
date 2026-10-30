"""
Authentication Blueprint for Echo Journal.
Handles registration, login, logout, session management, and scrypt verification.
"""

from functools import wraps
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    current_app,
    g
)
from .db import get_db_connection
from .repository import UserRepository
from .security import hash_password, verify_password, generate_csrf_token
from .validation import validate_registration
from .rate_limit import login_rate_limiter, registration_rate_limiter

auth_bp = Blueprint("auth", __name__)


def login_required(view):
    """Decorator ensuring view requires an active authenticated session."""
    @wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            flash("Please sign in to access your journal.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return view(**kwargs)
    return wrapped_view


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("journal.index"))

    if request.method == "POST":
        ip = request.remote_addr or "unknown"
        allowed, retry_after = registration_rate_limiter.record_attempt(ip)
        if not allowed:
            flash(f"Too many registration attempts. Please retry in {retry_after} seconds.", "error")
            return render_template("auth/register.html")

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("auth/register.html", username=username, email=email)

        is_valid, error_msg = validate_registration(username, email, password)
        if not is_valid:
            flash(error_msg, "error")
            return render_template("auth/register.html", username=username, email=email)

        conn = get_db_connection(current_app.config.get("DATABASE_PATH"))
        repo = UserRepository(conn)

        if repo.get_by_username(username):
            flash("Username is already taken. Please choose another.", "error")
            conn.close()
            return render_template("auth/register.html", username=username, email=email)

        if repo.get_by_email(email):
            flash("An account with that email already exists.", "error")
            conn.close()
            return render_template("auth/register.html", username=username, email=email)

        pw_hash = hash_password(password)
        user_id = repo.create_user(username=username, email=email, password_hash=pw_hash)
        conn.close()

        # Registration success: reset rate limit
        registration_rate_limiter.reset(ip)

        # Regenerate session and set user details
        session.clear()
        session["user_id"] = user_id
        session["username"] = username
        session["_csrf_token"] = generate_csrf_token()
        session.permanent = True

        flash("Welcome to Echo Journal! Your private space is ready.", "success")
        return redirect(url_for("journal.index"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("journal.index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        rate_key = f"{request.remote_addr or 'unknown'}:{identifier}"
        allowed, retry_after = login_rate_limiter.record_attempt(rate_key)
        if not allowed:
            flash(f"Too many failed login attempts. Please wait {retry_after} seconds before trying again.", "error")
            return render_template("auth/login.html", identifier=identifier)

        if not identifier or not password:
            flash("Please enter both username/email and password.", "error")
            return render_template("auth/login.html", identifier=identifier)

        conn = get_db_connection(current_app.config.get("DATABASE_PATH"))
        repo = UserRepository(conn)

        user = repo.get_by_email(identifier) or repo.get_by_username(identifier)
        conn.close()

        if user is None or not verify_password(password, user["password_hash"]):
            flash("Invalid credentials. Please verify your details.", "error")
            return render_template("auth/login.html", identifier=identifier)

        # Authentication success: reset failed attempts
        login_rate_limiter.reset(rate_key)

        # Session Fixation Defense: clear and regenerate session
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session["_csrf_token"] = generate_csrf_token()
        session.permanent = True

        next_url = request.args.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(url_for("journal.index"))

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    flash("You have been signed out safely.", "info")
    return redirect(url_for("auth.login"))
