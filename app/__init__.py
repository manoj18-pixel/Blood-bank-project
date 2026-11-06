"""BloodLink application factory."""

import os
from datetime import datetime
from pathlib import Path

import click
from flask import Flask, render_template
from flask_login import current_user

from app.config import DevelopmentConfig, config_by_name
from app.constants import BLOOD_GROUPS
from app.extensions import csrf, db, limiter, login_manager, mail, migrate
from app.utils.time import utcnow


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(config_name, DevelopmentConfig))
    try:
        Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    except OSError:
        # Serverless platforms (e.g. Vercel) mount the bundle read-only. A
        # PostgreSQL DATABASE_URL should be used there instead of SQLite.
        pass

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # Importing models registers the tables on the SQLAlchemy metadata.
    from app.models import Notification, User

    @login_manager.user_loader
    def load_user(user_id):  # pragma: no cover - exercised via client requests
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    # ---------------------------------------------------------- blueprints
    from app.blueprints.admin import bp as admin_bp
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.donors import bp as donors_bp
    from app.blueprints.main import bp as main_bp
    from app.blueprints.notifications import bp as notifications_bp
    from app.blueprints.offers import bp as offers_bp
    from app.blueprints.profile import bp as profile_bp
    from app.blueprints.requests import bp as requests_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(donors_bp, url_prefix="/donors")
    app.register_blueprint(requests_bp, url_prefix="/requests")
    app.register_blueprint(offers_bp)
    app.register_blueprint(profile_bp, url_prefix="/profile")
    app.register_blueprint(notifications_bp, url_prefix="/notifications")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # ------------------------------------------------------------- filters
    @app.template_filter("dt")
    def format_datetime(value, fmt="%d %b %Y, %I:%M %p"):
        if not value:
            return "-"
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return value
        return value.strftime(fmt)

    @app.template_filter("d")
    def format_date(value, fmt="%d %b %Y"):
        if not value:
            return "-"
        return value.strftime(fmt)

    @app.template_filter("timeago")
    def time_ago(value):
        if not value:
            return "-"
        seconds = max(0, int((utcnow() - value).total_seconds()))
        if seconds < 60:
            return "just now"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m ago"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h ago"
        days = hours // 24
        if days < 30:
            return f"{days}d ago"
        return value.strftime("%d %b %Y")

    # ------------------------------------------------------------ context
    @app.context_processor
    def inject_globals():
        unread = 0
        if current_user.is_authenticated:
            unread = Notification.query.filter_by(
                user_id=current_user.id, is_read=False
            ).count()
        return {
            "unread_notifications": unread,
            "current_year": utcnow().year,
            "BLOOD_GROUPS": BLOOD_GROUPS,
            "now": utcnow(),
        }

    # ------------------------------------------------------------- errors
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(410)
    def gone(error):
        return render_template("errors/410.html"), 410

    @app.errorhandler(429)
    def rate_limited(error):
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def server_error(error):  # pragma: no cover
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; font-src 'self'; frame-ancestors 'none'",
        )
        return response

    # ---------------------------------------------------------------- cli
    @app.cli.command("init-db")
    def init_db():  # pragma: no cover - CLI helper
        """Create all database tables."""
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("create-admin")
    @click.option("--email", prompt="Admin email")
    @click.option("--password", prompt="Admin password", hide_input=True, confirmation_prompt=True)
    @click.option("--name", prompt="Admin name", default="BloodLink Admin")
    def create_admin(email, password, name):  # pragma: no cover - CLI helper
        """Create (or promote) an administrator account."""
        from app.bootstrap import ensure_admin

        user = ensure_admin(email, password, name)
        click.echo(f"Admin ready: {user.email}")

    return app
