"""In-app notifications."""

from app.extensions import db
from app.utils.time import utcnow


class Notification(db.Model):
    __tablename__ = "notifications"
    __table_args__ = (
        db.Index("idx_notifications_user", "user_id", "is_read", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.String(40), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    body = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("User", back_populates="notifications")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Notification {self.type} user={self.user_id}>"
