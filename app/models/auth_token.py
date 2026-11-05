"""Single-use tokens for email verification and password reset."""

from app.extensions import db
from app.utils.time import utcnow


class AuthToken(db.Model):
    __tablename__ = "auth_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token_hash = db.Column(db.String(64), unique=True, nullable=False)
    purpose = db.Column(db.String(20), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("User")

    @property
    def is_valid(self) -> bool:
        return self.used_at is None and self.expires_at > utcnow()
