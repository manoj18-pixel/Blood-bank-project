"""A donor's offer on a blood request."""

from app.extensions import db
from app.utils.time import utcnow


class DonorResponse(db.Model):
    __tablename__ = "donor_responses"
    __table_args__ = (
        db.UniqueConstraint("request_id", "donor_id", name="uq_response_request_donor"),
        db.Index("idx_responses_request", "request_id", "status"),
        db.Index("idx_responses_donor", "donor_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(
        db.Integer, db.ForeignKey("blood_requests.id"), nullable=False
    )
    donor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(12), nullable=False, default="offered")
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    request = db.relationship("BloodRequest", back_populates="responses")
    donor = db.relationship("User", back_populates="responses", foreign_keys=[donor_id])

    @property
    def is_active_offer(self) -> bool:
        return self.status in {"offered", "accepted", "donated"}

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DonorResponse request={self.request_id} donor={self.donor_id} {self.status}>"
