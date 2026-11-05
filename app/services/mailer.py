"""Optional email delivery. In development links are logged instead."""

from flask import current_app
from flask_mail import Message

from app.extensions import mail


def send_email(subject: str, recipients: list[str], body: str) -> bool:
    if not current_app.config.get("MAIL_SERVER"):
        current_app.logger.info(
            "[mail disabled] to=%s subject=%s body=%s", recipients, subject, body
        )
        return False
    try:
        mail.send(Message(subject=subject, recipients=recipients, body=body))
        return True
    except Exception:  # pragma: no cover - depends on external SMTP
        current_app.logger.exception("Failed to send email to %s", recipients)
        return False
