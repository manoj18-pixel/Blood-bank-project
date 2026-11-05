"""Vercel serverless entry point for BloodLink.

Vercel runs each request in a short-lived Python function, so:
- all routes are rewritten to this module (see ``vercel.json``);
- ``DATABASE_URL`` must point to PostgreSQL (Neon, Vercel Postgres, ...);
- the schema is created on cold start because Vercel has no release phase.
"""

import os

from app import create_app
from app.extensions import db

if not os.environ.get("DATABASE_URL"):
    raise RuntimeError(
        "DATABASE_URL is required on Vercel. Create a PostgreSQL database "
        "(for example at https://neon.tech) and add its connection string in "
        "Vercel > Project > Settings > Environment Variables."
    )

app = create_app("production")

with app.app_context():
    db.create_all()
