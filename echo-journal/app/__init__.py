"""
Echo Journal Flask Application Factory.
Configures blueprints, secure cookies, CSRF protection, and security headers.
"""

import os

try:
    from flask import Flask, session, request, abort, render_template, g
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    Flask = object

from .db import get_db_connection, init_db
from .security import generate_csrf_token, verify_csrf_token


def create_app(test_config=None):
    if not HAS_FLASK:
        raise ImportError("Flask is required to run create_app. Please run: pip install -r requirements.txt")
    app = Flask(__name__, instance_relative_config=True)
    
    # Default Configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev_secret_key_change_in_production_32bytes!"),
        DATABASE_PATH=os.environ.get("DATABASE_PATH", "echo_journal.db"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "False").lower() == "true",
        PERMANENT_SESSION_LIFETIME=86400 * 7,  # 7 days
    )

    if test_config is not None:
        app.config.update(test_config)

    # Initialize Database Schema
    with app.app_context():
        conn = get_db_connection(app.config.get("DATABASE_PATH"))
        init_db(conn)
        conn.close()

    # Database connection teardown per request
    @app.teardown_appcontext
    def close_db(error):
        if hasattr(g, "db_conn"):
            g.db_conn.close()

    # Security Headers Middleware
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "script-src 'self';"
        )
        return response

    # CSRF Token Injection & Validation
    @app.before_request
    def csrf_protect():
        # Ensure session has a CSRF token
        if "_csrf_token" not in session:
            session["_csrf_token"] = generate_csrf_token()
            
        # Protect state-changing HTTP methods
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            # Exclude JSON API / test mode when explicitly bypassing
            if app.config.get("TESTING") and request.headers.get("X-Skip-CSRF"):
                return
                
            token = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
            session_token = session.get("_csrf_token")
            
            if not token or not session_token or not verify_csrf_token(token, session_token):
                abort(400, description="Invalid or missing CSRF token.")

    # Context Processor for Templates
    @app.context_processor
    def inject_csrf_token():
        return {
            "csrf_token": session.get("_csrf_token", ""),
            "current_user_id": session.get("user_id"),
            "current_username": session.get("username"),
        }

    # Register Blueprints
    from .auth import auth_bp
    from .journal import journal_bp
    from .account import account_bp
    from .insights import insights_bp
    from .admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(journal_bp)
    app.register_blueprint(account_bp, url_prefix="/account")
    app.register_blueprint(insights_bp, url_prefix="/insights")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.route("/")
    def index():
        from flask import redirect, url_for
        if "user_id" in session:
            return redirect(url_for("journal.index"))
        return redirect(url_for("auth.login"))

    return app
