"""Admin bootstrap from environment variables (Vercel has no shell)."""

from app.bootstrap import (
    DEFAULT_ADMIN_EMAIL,
    DEFAULT_ADMIN_PASSWORD,
    ensure_admin,
    ensure_admin_from_env,
    ensure_default_admin,
)
from app.models import User


def test_creates_admin_when_missing(app, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "Admin@Example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "SuperSecret@123")
    monkeypatch.setenv("ADMIN_NAME", "Site Owner")

    assert ensure_admin_from_env() is True

    user = User.query.filter_by(email="admin@example.com").one()
    assert user.role == "admin"
    assert user.email_verified is True
    assert user.status == "active"
    assert user.full_name == "Site Owner"
    assert user.is_donor is False
    assert user.check_password("SuperSecret@123")


def test_promotes_existing_user_and_resets_password(app, make_user):
    make_user(email="owner@example.com", password="Original@123")

    ensure_admin("owner@example.com", "Different@123")

    user = User.query.filter_by(email="owner@example.com").one()
    assert user.role == "admin"
    assert user.email_verified is True
    assert user.check_password("Different@123")
    assert not user.check_password("Original@123")


def test_returns_false_without_env(app, monkeypatch):
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

    assert ensure_admin_from_env() is False
    assert User.query.count() == 0


def test_returns_false_when_only_email_is_set(app, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

    assert ensure_admin_from_env() is False
    assert User.query.count() == 0


def test_is_idempotent(app, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "SuperSecret@123")

    ensure_admin_from_env()
    ensure_admin_from_env()

    assert User.query.filter_by(email="admin@example.com").count() == 1


def test_default_admin_is_created_when_env_is_absent(app):
    user = ensure_default_admin()

    assert user.email == DEFAULT_ADMIN_EMAIL
    assert user.role == "admin"
    assert user.email_verified is True
    assert user.check_password(DEFAULT_ADMIN_PASSWORD)
