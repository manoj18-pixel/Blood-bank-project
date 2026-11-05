"""Admin action audit trail."""

from app.extensions import db
from app.utils.time import utcnow


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(80), nullable=False)
    target = db.Column(db.String(120), nullable=True)
    meta = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    actor = db.relationship("User", foreign_keys=[actor_id])
