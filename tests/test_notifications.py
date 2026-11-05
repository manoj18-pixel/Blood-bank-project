"""Notification inbox tests (TC-NOTIF-*)."""

from app.extensions import db
from app.models import Notification
from app.services.notifications import notify


def make_notification(user, title="Test alert", link=None, is_read=False):
    notification = Notification(
        user_id=user.id,
        type="test",
        title=title,
        body="Something happened.",
        link=link,
        is_read=is_read,
    )
    db.session.add(notification)
    db.session.commit()
    return notification


def test_notifications_require_login(client):
    response = client.get("/notifications/")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_inbox_lists_only_own_notifications(client, make_user, login_as):
    me = make_user(email="me@example.com")
    other = make_user(email="other@example.com")
    make_notification(me, title="Mine is here")
    make_notification(other, title="Someone else's secret")

    login_as(client, me.email)
    body = client.get("/notifications/").get_data(as_text=True)

    assert "Mine is here" in body
    assert "Someone else's secret" not in body


def test_mark_read_redirects_to_link(client, make_user, login_as):
    user = make_user()
    notification = make_notification(user, link="/requests/")
    login_as(client, user.email)

    response = client.post(f"/notifications/{notification.id}/read")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/requests/")
    db.session.refresh(notification)
    assert notification.is_read is True


def test_mark_read_without_link_returns_to_inbox(client, make_user, login_as):
    user = make_user()
    notification = make_notification(user, link=None)
    login_as(client, user.email)

    response = client.post(f"/notifications/{notification.id}/read")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/notifications/")
    db.session.refresh(notification)
    assert notification.is_read is True


def test_cannot_mark_someone_elses_notification(client, make_user, login_as):
    me = make_user(email="me@example.com")
    other = make_user(email="other@example.com")
    notification = make_notification(other)
    login_as(client, me.email)

    response = client.post(f"/notifications/{notification.id}/read")

    assert response.status_code == 403
    db.session.refresh(notification)
    assert notification.is_read is False


def test_mark_all_read_only_affects_own_inbox(client, make_user, login_as):
    me = make_user(email="me@example.com")
    other = make_user(email="other@example.com")
    mine = make_notification(me)
    theirs = make_notification(other)
    login_as(client, me.email)

    response = client.post("/notifications/read-all")

    assert response.status_code == 302
    db.session.refresh(mine)
    db.session.refresh(theirs)
    assert mine.is_read is True
    assert theirs.is_read is False


def test_unread_count_api(client, make_user, login_as):
    user = make_user()
    make_notification(user)
    make_notification(user, is_read=True)
    login_as(client, user.email)

    payload = client.get("/notifications/api/unread-count").get_json()

    assert payload == {"count": 1}


def test_offer_notification_lands_in_requester_inbox(
    app, make_user, make_request, login_as
):
    requester = make_user(email="ravi@example.com", blood_group="A+", is_donor=False)
    donor = make_user(email="asha@example.com", blood_group="O-")
    blood_request = make_request(requester, blood_group="A+")

    donor_client = app.test_client()
    login_as(donor_client, donor.email)
    donor_client.post(f"/requests/{blood_request.id}/offer", data={"message": "hi"})

    notification = Notification.query.filter_by(user_id=requester.id).one()
    assert notification.type == "offer_received"
    assert str(blood_request.id) in notification.link

    requester_client = app.test_client()
    login_as(requester_client, requester.email)
    body = requester_client.get("/notifications/").get_data(as_text=True)
    assert "New donor offer" in body


def test_notify_helper_creates_row(app, make_user):
    user = make_user()

    notification = notify(user.id, "hello", "Hi", "Body text", link="/dashboard")

    assert notification.id is not None
    assert Notification.query.filter_by(user_id=user.id).count() == 1
