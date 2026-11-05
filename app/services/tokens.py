"""Single-use auth token creation and consumption."""

import hashlib
import secrets
from datetime import timedelta

from app.extensions import db
from app.models import AuthToken
from app.utils.time import utcnow


def _hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_token(user, purpose: str, expires_minutes: int = 60) -> str:
    raw = secrets.token_urlsafe(32)
    token = AuthToken(
        user_id=user.id,
        token_hash=_hash(raw),
        purpose=purpose,
        expires_at=utcnow() + timedelta(minutes=expires_minutes),
    )
    db.session.add(token)
    db.session.commit()
    return raw


def peek_token(raw_token: str, purpose: str) -> AuthToken | None:
    return (
        AuthToken.query.filter_by(
            token_hash=_hash(raw_token), purpose=purpose, used_at=None
        )
        .filter(AuthToken.expires_at > utcnow())
        .first()
    )


def consume_token(raw_token: str, purpose: str):
    token = peek_token(raw_token, purpose)
    if not token:
        return None
    token.used_at = utcnow()
    db.session.commit()
    return token.user
