"""Shared pytest fixtures."""

from datetime import timedelta

import pytest
from flask import g

from app import create_app
from app.extensions import db
from app.models import BloodRequest, User
from app.utils.time import utcnow

DEFAULT_PASSWORD = "Str0ngPass!23"


@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()

        # The fixture keeps an app context alive for the whole test, so Flask's
        # ``g`` is shared between requests. Flask-Login caches the signed-in
        # user on ``g``; clearing it ensures each request is authenticated from
        # its own client session (as it would be in production).
        @application.before_request
        def _clear_login_cache():
            g.pop("_login_user", None)

        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def make_user(app):
    def _make(
        email="asha@example.com",
        password=DEFAULT_PASSWORD,
        full_name="Asha Rao",
        blood_group="O-",
        city="Pune",
        phone="9222222222",
        is_donor=True,
        is_available=True,
        last_donation_date=None,
        status="active",
        role="user",
        date_of_birth=None,
        latitude=None,
        longitude=None,
    ):
        user = User(
            full_name=full_name,
            email=email.lower(),
            phone=phone,
            blood_group=blood_group,
            city=city,
            area="Kothrud",
            pincode="411038",
            latitude=latitude,
            longitude=longitude,
            is_donor=is_donor,
            is_available=is_available,
            last_donation_date=last_donation_date,
            email_verified=True,
            status=status,
            role=role,
            date_of_birth=date_of_birth,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    return _make


@pytest.fixture()
def make_request(app):
    def _make(requester, **kwargs):
        values = {
            "patient_name": "Test Patient",
            "blood_group": "A+",
            "units_needed": 1,
            "hospital_name": "Test Hospital",
            "address": "12 Test Road",
            "city": requester.city,
            "pincode": "411001",
            "urgency": "normal",
            "needed_by": utcnow() + timedelta(days=2),
            "contact_phone": "9111111111",
            "notes": "Test request",
            "status": "open",
        }
        values.update(kwargs)
        blood_request = BloodRequest(requester_id=requester.id, **values)
        db.session.add(blood_request)
        db.session.commit()
        return blood_request

    return _make


@pytest.fixture()
def login_as():
    def _login(client, email, password=DEFAULT_PASSWORD, follow=True):
        return client.post(
            "/auth/login",
            data={"email": email, "password": password},
            follow_redirects=follow,
        )

    return _login
