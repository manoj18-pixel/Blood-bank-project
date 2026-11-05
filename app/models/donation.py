"""Recorded blood donations."""

from app.extensions import db
from app.utils.time import utcnow


class Donation(db.Model):
    __tablename__ = "donations"
    __table_args__ = (db.Index("idx_donations_donor", "donor_id", "donated_on"),)

    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    request_id = db.Column(
        db.Integer, db.ForeignKey("blood_requests.id"), nullable=True
    )
    hospital_name = db.Column(db.String(160), nullable=True)
    donated_on = db.Column(db.Date, nullable=False)
    units = db.Column(db.Integer, nullable=False, default=1)
    notes = db.Column(db.Text, nullable=True)
    verified_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    donor = db.relationship("User", back_populates="donations", foreign_keys=[donor_id])
    request = db.relationship("BloodRequest", back_populates="donations")
    verifier = db.relationship("User", foreign_keys=[verified_by])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Donation donor={self.donor_id} {self.donated_on}>"
