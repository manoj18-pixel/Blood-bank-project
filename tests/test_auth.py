"""Authentication tests (TC-AUTH-*)."""

from app.extensions import db
from app.models import AuthToken, User

REGISTER_DATA = {
    "full_name": "New Donor",
    "email": "new@example.com",
    "phone": "9000000000",
    "blood_group": "A+",
    "city": "Pune",
    "area": "Baner",
    "pincode": "411045",
    "password": "Str0ngPass!23",
    "confirm_password": "Str0ngPass!23",
}


def test_register_hashes_password(client, app):
    response = client.post("/auth/register", data=REGISTER_DATA, follow_redirects=True)
    assert response.status_code == 200
    assert b"Your dashboard" in response.data or b"Dashboard" in response.data

    user = User.query.filter_by(email="new@example.com").first()
    assert user is not None
    assert user.password_hash != "Str0ngPass!23"
    assert user.check_password("Str0ngPass!23")
    assert user.email_verified is True


def test_duplicate_email_is_case_insensitive(client, make_user):
    make_user(email="Asha@Example.com")
    duplicate = dict(REGISTER_DATA, email="asha@example.com")

    response = client.post("/auth/register", data=duplicate)

    assert response.status_code == 200
    assert b"already exists" in response.data.lower()
    assert User.query.count() == 1


def test_weak_password_is_rejected(client):
    weak = dict(REGISTER_DATA, email="weak@example.com", password="123456", confirm_password="123456")
    response = client.post("/auth/register", data=weak)

    assert response.status_code == 200
    assert User.query.count() == 0


def test_password_mismatch_is_rejected(client):
    mismatch = dict(REGISTER_DATA, email="mismatch@example.com", confirm_password="Different!23")
    response = client.post("/auth/register", data=mismatch)

    assert response.status_code == 200
    assert User.query.count() == 0


def test_invalid_email_is_rejected(client):
    invalid = dict(REGISTER_DATA, email="not-an-email")
    response = client.post("/auth/register", data=invalid)

    assert response.status_code == 200
    assert User.query.count() == 0


def test_login_stores_user_id_in_session(client, make_user, login_as):
    user = make_user()
    login_as(client, user.email)

    with client.session_transaction() as session:
        assert session["_user_id"] == str(user.id)
        assert session["_fresh"] is True


def test_login_success(client, make_user, login_as):
    user = make_user()
    response = login_as(client, user.email)

    assert response.status_code == 200
    assert b"Your dashboard" in response.data


def test_login_accepts_existing_reserved_domain_account(
    client, make_user, login_as
):
    # The demo admin is seeded with a ``.local`` address. Registration rejects
    # that domain, but sign-in must still work for accounts already stored.
    admin = make_user(
        email="admin@bloodlink.local",
        full_name="Site Admin",
        is_donor=False,
        role="admin",
    )

    response = login_as(client, admin.email)

    assert response.status_code == 200
    assert client.get("/admin/").status_code == 200


def test_forgot_password_accepts_reserved_domain_account(client, make_user):
    user = make_user(email="admin@bloodlink.local")

    response = client.post("/auth/forgot", data={"email": user.email})

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]
    assert (
        AuthToken.query.filter_by(user_id=user.id, purpose="reset_password").count()
        == 1
    )


def test_login_wrong_password(client, make_user, login_as):
    user = make_user()
    response = login_as(client, user.email, password="WrongPass!23")

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data
    assert client.get("/dashboard").status_code == 302


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_logout_clears_session(client, make_user, login_as):
    user = make_user()
    login_as(client, user.email)

    response = client.post("/auth/logout", follow_redirects=True)

    assert response.status_code == 200
    assert client.get("/dashboard").status_code == 302


def test_suspended_user_cannot_login(client, make_user, login_as):
    user = make_user(status="suspended")
    response = login_as(client, user.email)

    assert response.status_code == 200
    assert b"suspended" in response.data.lower()
    assert client.get("/dashboard").status_code == 302


def test_email_verification_token_is_single_use(client, make_user, app):
    from app.services.tokens import consume_token, create_token

    user = make_user(email="verify@example.com")
    token = create_token(user, "verify_email")

    assert consume_token(token, "verify_email") is not None
    assert consume_token(token, "verify_email") is None


def test_reset_token_expiry_is_rejected(client, make_user):
    from datetime import timedelta

    from app.services.tokens import create_token
    from app.utils.time import utcnow

    user = make_user(email="reset@example.com")
    raw = create_token(user, "reset_password", expires_minutes=60)
    token = AuthToken.query.filter_by(purpose="reset_password").one()
    token.expires_at = utcnow() - timedelta(minutes=1)
    db.session.commit()

    response = client.get(f"/auth/reset/{raw}")

    assert response.status_code == 302
    assert "/auth/forgot" in response.headers["Location"]


def test_reset_token_is_single_use_through_route(client, make_user):
    from app.services.tokens import create_token

    user = make_user(email="reset@example.com")
    raw = create_token(user, "reset_password", expires_minutes=60)

    first = client.post(
        f"/auth/reset/{raw}",
        data={"password": "N3wStrong!23", "confirm_password": "N3wStrong!23"},
    )
    second = client.get(f"/auth/reset/{raw}")

    assert first.status_code == 302
    assert "/auth/login" in first.headers["Location"]
    assert second.status_code == 302
    assert "/auth/forgot" in second.headers["Location"]
    db.session.refresh(user)
    assert user.check_password("N3wStrong!23") is True


def test_role_injection_is_ignored(client):
    payload = dict(REGISTER_DATA, email="sneaky@example.com", role="admin", is_admin="1")
    client.post("/auth/register", data=payload, follow_redirects=True)

    user = User.query.filter_by(email="sneaky@example.com").first()
    assert user is not None
    assert user.role == "user"


def test_open_redirect_is_blocked(client, make_user, login_as):
    user = make_user()
    response = client.post(
        "/auth/login?next=//evil.example.com",
        data={"email": user.email, "password": "Str0ngPass!23"},
    )

    assert response.status_code == 302
    assert "evil.example.com" not in response.headers["Location"]
    assert response.headers["Location"].endswith("/dashboard")
