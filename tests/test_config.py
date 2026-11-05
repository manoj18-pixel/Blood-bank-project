"""Deployment configuration helpers."""

import pytest

from app.config import _database_uri


@pytest.fixture(autouse=True)
def clear_database_env(monkeypatch):
    """Keep these tests independent from the machine's environment."""
    for name in (
        "DATABASE_URL",
        "POSTGRES_URL",
        "POSTGRES_PRISMA_URL",
        "POSTGRES_URL_NON_POOLING",
    ):
        monkeypatch.delenv(name, raising=False)


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
    assert _database_uri().startswith("sqlite:///")


def test_postgres_url_is_used_when_database_url_is_missing(monkeypatch):
    monkeypatch.setenv("POSTGRES_URL", "postgres://user:pass@host/bloodlink")

    assert _database_uri() == "postgresql+psycopg://user:pass@host/bloodlink"


def test_vercel_postgres_url_non_pooling_is_used_as_last_resort(monkeypatch):
    monkeypatch.setenv(
        "POSTGRES_URL_NON_POOLING", "postgresql://user:pass@host:5432/bloodlink"
    )

    assert _database_uri() == "postgresql+psycopg://user:pass@host:5432/bloodlink"


def test_database_url_wins_over_postgres_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://a:b@primary/db")
    monkeypatch.setenv("POSTGRES_URL", "postgresql://a:b@fallback/db")

    assert _database_uri() == "postgresql+psycopg://a:b@primary/db"
