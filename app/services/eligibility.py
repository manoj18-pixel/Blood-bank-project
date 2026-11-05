"""Donor eligibility rules."""

from datetime import date, timedelta

from flask import current_app

REASON_LABELS = {
    "available": "Available to donate",
    "cooldown": "In donation cooldown",
    "unavailable": "Currently unavailable",
    "not_donor": "Not registered as a donor",
    "suspended": "Account suspended",
    "age": "Outside the 18-65 age range",
    "unverified": "Email not verified",
    "unknown": "Unknown donor",
}


def eligibility(user, as_of: date | None = None) -> tuple[bool, str]:
    """Return ``(can_donate_now, reason_code)`` for a user."""
    if user is None:
        return False, "unknown"

    as_of = as_of or date.today()

    if user.status != "active" or not getattr(user, "is_active", True):
        return False, "suspended"
    if not user.is_donor:
        return False, "not_donor"

    if current_app.config.get("REQUIRE_EMAIL_VERIFICATION") and not user.email_verified:
        return False, "unverified"

    age = user.age
    if age is not None and (age < 18 or age > 65):
        return False, "age"

    if not user.is_available:
        return False, "unavailable"

    cooldown = int(current_app.config.get("DONATION_COOLDOWN_DAYS", 90))
    if user.last_donation_date:
        days_since = (as_of - user.last_donation_date).days
        if days_since < cooldown:
            return False, "cooldown"

    return True, "available"


def is_eligible(user, as_of: date | None = None) -> bool:
    return eligibility(user, as_of)[0]


def eligible_from(user) -> date | None:
    """Date the donor becomes eligible again, if in cooldown."""
    if not user or not user.last_donation_date:
        return None
    cooldown = int(current_app.config.get("DONATION_COOLDOWN_DAYS", 90))
    return user.last_donation_date + timedelta(days=cooldown)


def cooldown_days_left(user, as_of: date | None = None) -> int:
    if not user or not user.last_donation_date:
        return 0
    as_of = as_of or date.today()
    cooldown = int(current_app.config.get("DONATION_COOLDOWN_DAYS", 90))
    return max(0, cooldown - (as_of - user.last_donation_date).days)


def reason_label(reason: str) -> str:
    return REASON_LABELS.get(reason, "Not eligible")
