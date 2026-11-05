"""Admin audit log helper."""

from app.extensions import db
from app.models import AuditLog


def log_action(actor_id: int, action: str, target: str | None = None, meta: str | None = None):
    entry = AuditLog(actor_id=actor_id, action=action, target=target, meta=meta)
    db.session.add(entry)
    db.session.commit()
    return entry
