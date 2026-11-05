"""Model package - importing this registers every table with SQLAlchemy."""

from app.models.audit_log import AuditLog
from app.models.auth_token import AuthToken
from app.models.blood_request import BloodRequest
from app.models.donation import Donation
from app.models.donor_response import DonorResponse
from app.models.notification import Notification
from app.models.user import User

__all__ = [
    "AuditLog",
    "AuthToken",
    "BloodRequest",
    "Donation",
    "DonorResponse",
    "Notification",
    "User",
]
