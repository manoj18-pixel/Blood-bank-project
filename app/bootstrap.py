"""Administrator bootstrap helpers.

Used by:
- the ``create-admin`` Flask CLI command, and
- the Vercel entry point (``index.py``), which promotes/creates the account
  configured through ``ADMIN_EMAIL`` / ``ADMIN_PASSWORD`` on cold start.

Deploying an admin this way avoids needing a shell on serverless platforms.
"""

import os

from app.extensions import db
from app.models import User

# Built-in demo administrator. Used only when ADMIN_EMAIL / ADMIN_PASSWORD are
# not configured. Change the password from the profile page after signing in.
DEFAULT_ADMIN_EMAIL = "admin@bloodlink.local"
DEFAULT_ADMIN_PASSWORD = "Bl-IE0AyZGh6-6lduxB!9"
DEFAULT_ADMIN_NAME = "BloodLink Admin"


def ensure_admin(email: str, password: str, full_name: str = "BloodLink Admin") -> User:
    """Create the admin account, or promote an existing account.

    The password is only written when the account is created. Existing accounts
    keep their current password so users can change it from the profile page
    without it being reset on the next deployment.
    """
    email = email.strip().lower()
    user = User.query.filter_by(email=email).first()

    if user is None:
        user = User(
            full_name=full_name,
            email=email,
            phone="0000000000",
            blood_group="O+",
            city="Pune",
            is_donor=False,
            email_verified=True,
            role="admin",
            status="active",
        )
        user.set_password(password)
        db.session.add(user)
    else:
        user.role = "admin"
        user.email_verified = True
        user.status = "active"

    db.session.commit()
    return user


def ensure_admin_from_env() -> bool:
    """Apply ``ADMIN_EMAIL`` / ``ADMIN_PASSWORD`` when both are configured."""
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    if not email or not password:
        return False

    ensure_admin(
        email,
        password,
        os.environ.get("ADMIN_NAME", "BloodLink Admin"),
    )
    return True


def ensure_default_admin() -> User:
    """Create the built-in demo admin (used when env credentials are absent)."""
    return ensure_admin(
        DEFAULT_ADMIN_EMAIL,
        DEFAULT_ADMIN_PASSWORD,
        DEFAULT_ADMIN_NAME,
    )
