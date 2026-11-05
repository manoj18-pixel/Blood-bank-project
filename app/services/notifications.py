"""Notification helpers."""

from app.extensions import db
from app.models import Notification


def notify(
    user_id: int,
    type: str,
    title: str,
    body: str,
    link: str | None = None,
    commit: bool = True,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        link=link,
    )
    db.session.add(notification)
    if commit:
        db.session.commit()
    return notification
