"""Vercel serverless entry point for BloodLink.

Vercel's zero-configuration Flask support looks for a module named ``index.py``
(or ``app.py``/``main.py``/``wsgi.py``) in the repository root that defines a
Flask instance called ``app``. Vercel turns that instance into one function and
routes every non-static request to it.

Notes for this deployment target:

- Data must live in PostgreSQL. ``DATABASE_URL`` (Neon / Vercel Postgres) is
  used when present; ``POSTGRES_URL`` is accepted as a fallback.
- If no PostgreSQL URL is configured the app falls back to SQLite in ``/tmp`` so
  the site still loads for a quick demo. ``/tmp`` is ephemeral: accounts and
  requests disappear when the function instance is recycled.
- Vercel has no release phase, so the schema is created on cold start. The
  operation is idempotent.
- Set ``ADMIN_EMAIL`` and ``ADMIN_PASSWORD`` to create (or promote) the
  administrator automatically on the first cold start.
"""

import logging
import os
import tempfile


def _prepare_database_url() -> None:
    """Make sure a writable database is configured before the app is created."""
    if os.environ.get("DATABASE_URL") or any(
        os.environ.get(name)
        for name in ("POSTGRES_URL", "POSTGRES_PRISMA_URL", "POSTGRES_URL_NON_POOLING")
    ):
        return

    if os.environ.get("VERCEL"):
        # The deployed bundle is read-only; the OS temp directory (/tmp) is the
        # only writable location.
        db_path = os.path.join(tempfile.gettempdir(), "bloodlink.db")
        os.environ["DATABASE_URL"] = "sqlite:///" + db_path.replace("\\", "/")
        logging.getLogger(__name__).warning(
            "No PostgreSQL URL found. Using ephemeral SQLite at %s. "
            "Add DATABASE_URL in Vercel project settings for persistent data.",
            db_path,
        )


_prepare_database_url()

# Imported after the environment is prepared because configuration is read at
# import time in app/config.py.
from app import create_app  # noqa: E402
from app.bootstrap import ensure_admin_from_env, ensure_default_admin  # noqa: E402
from app.extensions import db  # noqa: E402

app = create_app("production")

with app.app_context():
    db.create_all()
    if not ensure_admin_from_env():
        ensure_default_admin()
