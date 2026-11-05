"""Shared constants for BloodLink."""

BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")
BLOOD_GROUP_CHOICES = [(group, group) for group in BLOOD_GROUPS]

URGENCY_LEVELS = ("normal", "urgent", "critical")
URGENCY_CHOICES = [(level, level.title()) for level in URGENCY_LEVELS]

GENDERS = ("male", "female", "other")
GENDER_CHOICES = [("", "Prefer not to say")] + [(g, g.title()) for g in GENDERS]

REQUEST_STATUSES = ("open", "matched", "fulfilled", "cancelled", "expired")
RESPONSE_STATUSES = ("offered", "accepted", "declined", "withdrawn", "donated")

PER_PAGE = 20
