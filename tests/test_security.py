"""Security and privacy hardening tests (TC-SEC-*)."""

import json

from app.extensions import db
from app.models import User


def test_security_headers_are_present(client):
    response = client.get("/")

    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    csp = response.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


def test_public_home_page_hides_personal_data(client, make_user):
    donor = make_user(email="secret@example.com", phone="9876543210")

    body = client.get("/").get_data(as_text=True)

    assert donor.phone not in body
    assert donor.email not in body


def test_api_stats_is_public_and_anonymous(client, make_user):
    make_user()

    response = client.get("/api/stats")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["users"] == 1
    assert payload["donors"] == 1
    serialised = json.dumps(payload)
    assert "9876543210" not in serialised


def test_password_is_never_stored_in_plain_text(client, make_user):
    user = make_user(password="Str0ngPass!23")

    assert user.password_hash != "Str0ngPass!23"
    assert user.password_hash.startswith(("scrypt:", "pbkdf2:", "argon2"))
    assert user.check_password("Str0ngPass!23") is True
    assert user.check_password("wrong") is False


def test_login_cookie_is_httponly_and_samesite(client, make_user):
    user = make_user()

    response = client.post(
        "/auth/login",
        data={"email": user.email, "password": "Str0ngPass!23"},
    )

    cookie = response.headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_donor_profile_masks_phone_from_other_users(client, make_user, login_as):
    viewer = make_user(email="viewer@example.com", is_donor=False)
    donor = make_user(email="donor@example.com", phone="9876543210")
    login_as(client, viewer.email)

    body = client.get(f"/donors/{donor.id}").get_data(as_text=True)

    assert donor.phone not in body
    assert donor.masked_phone in body
    assert donor.email not in body


def test_donor_profile_shows_own_phone(client, make_user, login_as):
    donor = make_user(email="donor@example.com", phone="9876543210")
    login_as(client, donor.email)

    body = client.get(f"/donors/{donor.id}").get_data(as_text=True)

    assert donor.phone in body


def test_suspended_donor_profile_returns_404(client, make_user, login_as):
    viewer = make_user(email="viewer@example.com", is_donor=False)
    donor = make_user(email="gone@example.com", status="suspended")
    login_as(client, viewer.email)

    assert client.get(f"/donors/{donor.id}").status_code == 404


def test_public_request_page_hides_requester_phone(client, make_user, make_request, login_as):
    owner = make_user(email="owner@example.com", is_donor=False)
    viewer = make_user(email="viewer@example.com", is_donor=False)
    blood_request = make_request(owner, contact_phone="9555555555")
    login_as(client, viewer.email)

    body = client.get(f"/requests/{blood_request.id}").get_data(as_text=True)

    assert "9555555555" not in body
    assert "only after" in body.lower()


def test_unknown_route_renders_404_page(client):
    response = client.get("/this-does-not-exist")

    assert response.status_code == 404
    assert b"Page not found" in response.data


def test_anonymous_cannot_reach_admin_or_profile(client):
    for path in ("/admin/", "/profile/", "/notifications/", "/requests/"):
        response = client.get(path)
        assert response.status_code == 302, path
        assert "/auth/login" in response.headers["Location"], path


def test_role_cannot_be_escalated_through_profile(client, make_user, login_as):
    user = make_user(email="user@example.com", role="user")
    login_as(client, user.email)

    client.post(
        "/profile/",
        data={
            "full_name": user.full_name,
            "phone": user.phone,
            "blood_group": user.blood_group,
            "city": user.city,
            "role": "admin",
            "is_donor": "y",
            "is_available": "y",
        },
    )

    db.session.refresh(user)
    assert user.role == "user"
    assert client.get("/admin/").status_code == 403


def test_donor_json_api_requires_authentication(client):
    response = client.get("/donors/api/search")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_user_public_dict_excludes_private_fields(app, make_user):
    donor = make_user(email="private@example.com", phone="9876543210")

    payload = donor.to_public_dict()
    serialised = json.dumps(payload)

    assert donor.phone not in serialised
    assert donor.email not in serialised
    assert "phone" not in payload
    assert "email" not in payload
    assert payload["id"] == donor.id
