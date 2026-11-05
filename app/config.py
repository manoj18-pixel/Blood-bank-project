"""Application configuration classes."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _database_uri() -> str:
    """Return the configured database URL with a psycopg3-friendly scheme.

    Hosting providers (Render, Heroku, ...) often hand out ``postgres://`` or
    ``postgresql://`` URLs. SQLAlchemy needs an explicit driver, and the project
    ships with psycopg 3 in ``requirements-prod.txt``.
    """
    url = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{(INSTANCE_DIR / 'bloodlink.db').as_posix()}",
    )
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-this-in-production")

    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Business rules
    DONATION_COOLDOWN_DAYS = int(os.environ.get("DONATION_COOLDOWN_DAYS", "90"))
    PER_PAGE = int(os.environ.get("PER_PAGE", "20"))
    REQUIRE_EMAIL_VERIFICATION = _as_bool(
        os.environ.get("REQUIRE_EMAIL_VERIFICATION"), default=False
    )

    # Sessions / forms
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _as_bool(os.environ.get("SESSION_COOKIE_SECURE"), default=False)
    REMEMBER_COOKIE_HTTPONLY = True
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024

    # Rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

    # Mail (optional in development). When no server is configured links are logged.
    MAIL_SERVER = os.environ.get("MAIL_SERVER") or None
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = _as_bool(os.environ.get("MAIL_USE_TLS"), default=True)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME") or None
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD") or None
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "no-reply@bloodlink.local")
    MAIL_SUPPRESS_SEND = _as_bool(os.environ.get("MAIL_SUPPRESS_SEND"), default=True)

    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@bloodlink.local")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    MAIL_SUPPRESS_SEND = True
    REQUIRE_EMAIL_VERIFICATION = False
    SQLALCHEMY_ENGINE_OPTIONS = {}


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
