"""Small time helpers.

The application stores naive UTC datetimes so behaviour is identical on
SQLite and PostgreSQL.
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
