"""Blood request model."""

from app.extensions import db
from app.utils.time import utcnow


class BloodRequest(db.Model):
    __tablename__ = "blood_requests"
    __table_args__ = (
        db.Index("idx_requests_search", "status", "blood_group", "city", "needed_by"),
        db.Index("idx_requests_owner", "requester_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    patient_name = db.Column(db.String(80), nullable=False)
    patient_age = db.Column(db.Integer, nullable=True)
    blood_group = db.Column(db.String(3), nullable=False)
    units_needed = db.Column(db.Integer, nullable=False, default=1)
    hospital_name = db.Column(db.String(160), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    pincode = db.Column(db.String(10), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    urgency = db.Column(db.String(10), nullable=False, default="normal")
    needed_by = db.Column(db.DateTime, nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(12), nullable=False, default="open")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    fulfilled_at = db.Column(db.DateTime, nullable=True)

    requester = db.relationship("User", back_populates="requests", foreign_keys=[requester_id])
    responses = db.relationship(
        "DonorResponse",
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="DonorResponse.created_at.desc()",
    )
    donations = db.relationship("Donation", back_populates="request")

    # -------------------------------------------------------------- helpers
    @property
    def is_open(self) -> bool:
        return self.status == "open"

    @property
    def is_active_request(self) -> bool:
        return self.status in {"open", "matched"}

    @property
    def accepted_response(self):
        return next((r for r in self.responses if r.status in {"accepted", "donated"}), None)

    @property
    def units_remaining(self) -> int:
        donated = sum(d.units for d in self.donations)
        return max(0, self.units_needed - donated)

    @property
    def compatible_donor_groups(self) -> list[str]:
        from app.services.matching import compatible_donor_groups

        return compatible_donor_groups(self.blood_group)

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "patient_name": self.patient_name,
            "blood_group": self.blood_group,
            "units_needed": self.units_needed,
            "hospital_name": self.hospital_name,
            "city": self.city,
            "area": self.address,
            "urgency": self.urgency,
            "needed_by": self.needed_by.isoformat(),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<BloodRequest #{self.id} {self.blood_group} {self.status}>"
