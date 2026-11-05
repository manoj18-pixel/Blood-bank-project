"""Profile and availability tests (TC-PROF-*)."""

from datetime import date, timedelta

from app.extensions import db
from app.models import User


def profile_payload(user, **overrides):
    payload = {
        "full_name": user.full_name,
        "phone": user.phone,
        "blood_group": user.blood_group,
        "date_of_birth": "",
        "gender": "",
        "city": user.city,
        "area": user.area or "",
        "pincode": user.pincode or "",
        "last_donation_date": "",
        "is_donor": "y",
        "is_available": "y",
    }
    payload.update(overrides)
    return payload


def test_profile_requires_login(client):
    response = client.get("/profile/")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_profile_page_loads(client, make_user, login_as):
    user = make_user()
    login_as(client, user.email)

    response = client.get("/profile/")

    assert response.status_code == 200
    assert b"My profile" in response.data


def test_user_can_change_blood_group(client, make_user, login_as):
    user = make_user(blood_group="O-")
    login_as(client, user.email)

    response = client.post(
        "/profile/",
        data=profile_payload(user, blood_group="AB+"),
        follow_redirects=True,
    )

    assert response.status_code == 200
    db.session.refresh(user)
    assert user.blood_group == "AB+"
    assert b"Profile updated" in response.data


def test_invalid_blood_group_is_rejected(client, make_user, login_as):
    user = make_user(blood_group="O-")
    login_as(client, user.email)

    response = client.post("/profile/", data=profile_payload(user, blood_group="Z+"))

    assert response.status_code == 200
    db.session.refresh(user)
    assert user.blood_group == "O-"


def test_future_last_donation_date_is_rejected(client, make_user, login_as):
    user = make_user()
    login_as(client, user.email)
    future = (date.today() + timedelta(days=30)).isoformat()

    response = client.post(
        "/profile/",
        data=profile_payload(user, last_donation_date=future),
    )

    assert response.status_code == 200
    assert b"future" in response.data.lower()
    db.session.refresh(user)
    assert user.last_donation_date is None


def test_future_date_of_birth_is_rejected(client, make_user, login_as):
    user = make_user()
    login_as(client, user.email)
    future = (date.today() + timedelta(days=1)).isoformat()

    response = client.post(
        "/profile/", data=profile_payload(user, date_of_birth=future)
    )

    assert response.status_code == 200
    assert b"future" in response.data.lower()
    db.session.refresh(user)
    assert user.date_of_birth is None


def test_user_can_set_donation_and_availability(client, make_user, login_as):
    user = make_user(is_available=True)
    login_as(client, user.email)
    past = (date.today() - timedelta(days=10)).isoformat()

    client.post(
        "/profile/",
        data=profile_payload(
            user, last_donation_date=past, is_available="", is_donor="y"
        ),
    )

    db.session.refresh(user)
    assert user.last_donation_date == date.today() - timedelta(days=10)
    assert user.is_available is False
    assert user.eligibility[0] is False
    assert user.eligibility[1] == "unavailable"


def test_availability_toggle(client, make_user, login_as):
    user = make_user(is_available=True)
    login_as(client, user.email)

    client.post("/profile/availability")
    db.session.refresh(user)
    assert user.is_available is False

    client.post("/profile/availability")
    db.session.refresh(user)
    assert user.is_available is True


def test_requester_can_opt_into_donor_mode(client, make_user, login_as):
    user = make_user(is_donor=False)
    login_as(client, user.email)

    client.post(
        "/profile/",
        data=profile_payload(user, is_donor="y", is_available="y"),
    )

    db.session.refresh(user)
    assert user.is_donor is True


def test_change_password_requires_current_password(client, make_user, login_as):
    user = make_user()
    login_as(client, user.email)
    old_hash = user.password_hash

    response = client.post(
        "/profile/password",
        data={
            "current_password": "WrongPass!23",
            "new_password": "N3wStrong!23",
            "confirm_password": "N3wStrong!23",
        },
        follow_redirects=True,
    )

    assert b"current password is incorrect" in response.data.lower()
    db.session.refresh(user)
    assert user.password_hash == old_hash


def test_change_password_success(client, make_user, login_as):
    user = make_user()
    login_as(client, user.email)

    response = client.post(
        "/profile/password",
        data={
            "current_password": "Str0ngPass!23",
            "new_password": "N3wStrong!23",
            "confirm_password": "N3wStrong!23",
        },
        follow_redirects=True,
    )

    assert b"Password changed" in response.data
    db.session.refresh(user)
    assert user.check_password("N3wStrong!23") is True
    assert user.check_password("Str0ngPass!23") is False
