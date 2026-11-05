"""Administrator console tests (TC-ADMIN-*)."""

from app.extensions import db
from app.models import AuditLog, BloodRequest, Donation, DonorResponse, Notification, User


def admin_user(make_user):
    return make_user(
        email="admin@example.com",
        full_name="Site Admin",
        blood_group="O+",
        is_donor=False,
        role="admin",
    )


def test_admin_pages_require_login(client):
    response = client.get("/admin/")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_non_admin_is_forbidden(client, make_user, login_as):
    user = make_user(email="regular@example.com", is_donor=False)
    login_as(client, user.email)

    for path in ("/admin/", "/admin/users", "/admin/requests"):
        response = client.get(path)
        assert response.status_code == 403, path


def test_admin_dashboard_loads(client, make_user, login_as):
    admin = admin_user(make_user)
    login_as(client, admin.email)

    response = client.get("/admin/")

    assert response.status_code == 200
    assert b"Platform overview" in response.data


def test_admin_can_suspend_user_and_login_is_blocked(
    client, make_user, make_request, login_as
):
    admin = admin_user(make_user)
    victim = make_user(email="victim@example.com")
    owner = make_user(email="owner@example.com", is_donor=False)
    blood_request = make_request(owner)
    offer = DonorResponse(
        request_id=blood_request.id, donor_id=victim.id, status="offered"
    )
    db.session.add(offer)
    db.session.commit()
    login_as(client, admin.email)

    response = client.post(f"/admin/users/{victim.id}/suspend")

    assert response.status_code == 302
    db.session.refresh(victim)
    db.session.refresh(offer)
    assert victim.status == "suspended"
    assert offer.status == "withdrawn"
    assert Notification.query.filter_by(user_id=victim.id).count() == 1
    assert Notification.query.filter_by(user_id=owner.id).count() == 1
    assert AuditLog.query.filter_by(action="suspend_user").count() == 1

    victim_client = client.application.test_client()
    blocked = victim_client.post(
        "/auth/login",
        data={"email": victim.email, "password": "Str0ngPass!23"},
        follow_redirects=True,
    )
    assert b"suspended" in blocked.data.lower()
    assert victim_client.get("/dashboard").status_code == 302


def test_admin_can_reactivate_user(client, make_user, login_as):
    admin = admin_user(make_user)
    victim = make_user(email="victim@example.com", status="suspended")
    login_as(client, admin.email)

    client.post(f"/admin/users/{victim.id}/suspend")

    db.session.refresh(victim)
    assert victim.status == "active"


def test_admin_cannot_suspend_self(client, make_user, login_as):
    admin = admin_user(make_user)
    login_as(client, admin.email)

    client.post(f"/admin/users/{admin.id}/suspend", follow_redirects=True)

    db.session.refresh(admin)
    assert admin.status == "active"


def test_admin_can_verify_user(client, make_user, login_as):
    admin = admin_user(make_user)
    user = make_user(email="unverified@example.com")
    user.email_verified = False
    db.session.commit()
    login_as(client, admin.email)

    response = client.post(f"/admin/users/{user.id}/verify")

    assert response.status_code == 302
    db.session.refresh(user)
    assert user.email_verified is True
    assert AuditLog.query.filter_by(action="verify_user").count() == 1


def test_admin_can_remove_request(client, make_user, make_request, login_as):
    admin = admin_user(make_user)
    owner = make_user(email="owner@example.com", is_donor=False)
    blood_request = make_request(owner)
    login_as(client, admin.email)

    response = client.post(f"/admin/requests/{blood_request.id}/remove")

    assert response.status_code == 302
    db.session.refresh(blood_request)
    assert blood_request.status == "cancelled"
    assert Notification.query.filter_by(user_id=owner.id).count() == 1
    assert AuditLog.query.filter_by(action="remove_request").count() == 1


def test_removing_closed_request_is_refused(
    client, make_user, make_request, login_as
):
    admin = admin_user(make_user)
    owner = make_user(email="owner@example.com", is_donor=False)
    blood_request = make_request(owner, status="fulfilled")
    login_as(client, admin.email)

    response = client.post(
        f"/admin/requests/{blood_request.id}/remove", follow_redirects=True
    )

    assert response.status_code == 200
    db.session.refresh(blood_request)
    assert blood_request.status == "fulfilled"


def test_admin_role_cannot_be_downgraded_through_profile(
    client, make_user, login_as
):
    admin = admin_user(make_user)
    login_as(client, admin.email)

    client.post(
        "/profile/",
        data={
            "full_name": admin.full_name,
            "phone": admin.phone,
            "blood_group": admin.blood_group,
            "city": admin.city,
            "role": "user",
            "is_donor": "y",
            "is_available": "y",
        },
    )

    db.session.refresh(admin)
    assert admin.role == "admin"


def test_admin_dashboard_stats(client, make_user, make_request, login_as):
    admin = admin_user(make_user)
    owner = make_user(email="owner@example.com", is_donor=False)
    make_request(owner, status="open")
    make_request(owner, patient_name="Second", status="matched")
    login_as(client, admin.email)

    body = client.get("/admin/").get_data(as_text=True)

    assert "Total accounts" in body
    assert "Matched requests" in body
    assert "Platform overview" in body


def test_user_search_filters_results(client, make_user, login_as):
    admin = admin_user(make_user)
    make_user(email="findme@example.com", full_name="Find Me", city="Pune")
    make_user(email="hidden@example.com", full_name="Hidden Person", city="Mumbai")
    login_as(client, admin.email)

    body = client.get("/admin/users?q=Find").get_data(as_text=True)

    assert "Find Me" in body
    assert "Hidden Person" not in body


def test_admin_request_filter(client, make_user, make_request, login_as):
    admin = admin_user(make_user)
    owner = make_user(email="owner@example.com", is_donor=False)
    make_request(owner, patient_name="Open Patient", status="open")
    make_request(owner, patient_name="Done Patient", status="fulfilled")
    login_as(client, admin.email)

    body = client.get("/admin/requests?status=fulfilled").get_data(as_text=True)

    assert "Done Patient" in body
    assert "Open Patient" not in body
