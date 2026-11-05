"""User / donor account model."""

from datetime import date, timedelta

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.utils.time import utcnow


class User(UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = (
        db.Index("idx_users_match", "blood_group", "city", "is_available", "status"),
        db.Index("idx_users_city", "city"),
    )

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    blood_group = db.Column(db.String(3), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    city = db.Column(db.String(80), nullable=False)
    area = db.Column(db.String(120), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    is_donor = db.Column(db.Boolean, nullable=False, default=True)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    last_donation_date = db.Column(db.Date, nullable=True)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    role = db.Column(db.String(10), nullable=False, default="user")
    status = db.Column(db.String(12), nullable=False, default="active")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    requests = db.relationship(
        "BloodRequest",
        back_populates="requester",
        foreign_keys="BloodRequest.requester_id",
        cascade="all, delete-orphan",
    )
    responses = db.relationship(
        "DonorResponse",
        back_populates="donor",
        foreign_keys="DonorResponse.donor_id",
        cascade="all, delete-orphan",
    )
    donations = db.relationship(
        "Donation",
        back_populates="donor",
        foreign_keys="Donation.donor_id",
        cascade="all, delete-orphan",
        order_by="Donation.donated_on.desc()",
    )
    notifications = db.relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Notification.created_at.desc()",
    )

    # ------------------------------------------------------------------ auth
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self) -> bool:
        """Flask-Login uses this to block suspended accounts."""
        return self.status == "active"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    # ------------------------------------------------------------- profile
    @property
    def age(self) -> int | None:
        if not self.date_of_birth:
            return None
        today = date.today()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    @property
    def masked_phone(self) -> str:
        phone = self.phone or ""
        if len(phone) <= 4:
            return "*" * len(phone)
        return f"{phone[:2]}{'*' * (len(phone) - 4)}{phone[-2:]}"

    @property
    def initials(self) -> str:
        parts = [part for part in (self.full_name or "").split() if part]
        return "".join(part[0].upper() for part in parts[:2]) or "?"

    @property
    def donation_count(self) -> int:
        return len(self.donations)

    @property
    def eligibility(self):
        """Return ``(eligible, reason)`` - see ``services.eligibility``."""
        from app.services.eligibility import eligibility

        return eligibility(self)

    @property
    def eligible_from(self) -> date | None:
        from app.services.eligibility import eligible_from

        return eligible_from(self)

    @property
    def cooldown_days_left(self) -> int:
        remaining = self.eligible_from
        if not remaining:
            return 0
        return max(0, (remaining - date.today()).days)

    # --------------------------------------------------------- serialising
    def to_public_dict(self) -> dict:
        """Safe representation: never contains email, phone or address."""
        from app.services.eligibility import eligibility

        ok, reason = eligibility(self)
        return {
            "id": self.id,
            "full_name": self.full_name,
            "blood_group": self.blood_group,
            "city": self.city,
            "area": self.area,
            "is_available": self.is_available,
            "eligible": ok,
            "eligibility_reason": reason,
            "last_donation_date": (
                self.last_donation_date.isoformat() if self.last_donation_date else None
            ),
            "donation_count": self.donation_count,
            "member_since": self.created_at.date().isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<User {self.email} {self.blood_group}>"
