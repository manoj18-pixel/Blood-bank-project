"""Deployment configuration helpers."""

from app.config import _database_uri


def test_postgres_scheme_gets_psycopg_driver(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@host:5432/bloodlink")

    assert _database_uri() == "postgresql+psycopg://user:pass@host:5432/bloodlink"


def test_postgresql_scheme_gets_psycopg_driver(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host/bloodlink")

    assert _database_uri() == "postgresql+psycopg://user:pass@host/bloodlink"


def test_explicit_driver_is_left_alone(monkeypatch):
    url = "postgresql+psycopg://user:pass@host/bloodlink"
    monkeypatch.setenv("DATABASE_URL", url)

    assert _database_uri() == url


def test_sqlite_is_the_default(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert _database_uri().startswith("sqlite:///")
