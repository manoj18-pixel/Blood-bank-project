"""Donor search tests (TC-SRCH-*)."""

import json
from datetime import date, timedelta
from urllib.parse import urlencode

from app.models import User


def test_search_filters_to_compatible_groups(client, make_user, login_as):
    requester = make_user(email="ravi@example.com", blood_group="A+", is_donor=False)
    make_user(email="aplus@example.com", full_name="A Plus", blood_group="A+")
    make_user(email="aminus@example.com", full_name="A Minus", blood_group="A-")
    make_user(email="oplus@example.com", full_name="O Plus", blood_group="O+")
    make_user(email="ominus@example.com", full_name="O Minus", blood_group="O-")
    make_user(email="bplus@example.com", full_name="B Plus", blood_group="B+")
    login_as(client, requester.email)

    response = client.get("/donors/?" + urlencode({"group": "A+"}))

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "A Plus" in body
    assert "A Minus" in body
    assert "O Plus" in body
    assert "O Minus" in body
    assert "B Plus" not in body


def test_anonymous_cannot_search_donors(client):
    response = client.get("/donors/")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_city_filter_is_case_insensitive(client, make_user, login_as):
    requester = make_user(email="ravi@example.com", is_donor=False)
    make_user(email="pune@example.com", full_name="Pune Donor", city="Pune")
    make_user(email="mumbai@example.com", full_name="Mumbai Donor", city="Mumbai")
    login_as(client, requester.email)

    response = client.get("/donors/?city=pune")

    body = response.get_data(as_text=True)
    assert "Pune Donor" in body
    assert "Mumbai Donor" not in body


def test_unavailable_donor_is_hidden_by_default(client, make_user, login_as):
    requester = make_user(email="ravi@example.com", is_donor=False)
    make_user(email="away@example.com", full_name="Away Donor", is_available=False)
    login_as(client, requester.email)

    default = client.get("/donors/").get_data(as_text=True)
    included = client.get("/donors/?include_unavailable=1").get_data(as_text=True)

    assert "Away Donor" not in default
    assert "Away Donor" in included


def test_donor_in_cooldown_is_hidden_by_default(client, make_user, login_as):
    requester = make_user(email="ravi@example.com", is_donor=False)
    make_user(
        email="cooldown@example.com",
        full_name="Cooldown Donor",
        last_donation_date=date.today() - timedelta(days=10),
    )
    login_as(client, requester.email)

    default = client.get("/donors/").get_data(as_text=True)
    included = client.get("/donors/?include_unavailable=1").get_data(as_text=True)

    assert "Cooldown Donor" not in default
    assert "Cooldown Donor" in included


def test_json_search_never_exposes_private_fields(client, make_user, login_as):
    requester = make_user(email="ravi@example.com", is_donor=False)
    donor = make_user(email="private@example.com", phone="9876543210")
    login_as(client, requester.email)

    response = client.get("/donors/api/search")
    payload = response.get_json()
    serialised = json.dumps(payload)

    assert response.status_code == 200
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] == donor.id
    for private_value in (donor.phone, donor.email, "password_hash"):
        assert private_value not in serialised
    assert "phone" not in payload["items"][0]
    assert "email" not in payload["items"][0]


def test_search_uses_literal_city_for_sql_injection(client, make_user, login_as):
    requester = make_user(email="ravi@example.com", is_donor=False)
    make_user(email="safe@example.com", full_name="Safe Donor")
    login_as(client, requester.email)

    response = client.get("/donors/?city=' OR 1=1 --")

    assert response.status_code == 200
    assert User.query.count() == 2
    assert b"Safe Donor" not in response.data


def test_pagination_pages_are_disjoint(app, client, make_user, login_as):
    app.config["PER_PAGE"] = 2
    requester = make_user(email="ravi@example.com", is_donor=False)
    for index, name in enumerate(("Donor One", "Donor Two", "Donor Three")):
        make_user(email=f"donor{index}@example.com", full_name=name)
    login_as(client, requester.email)

    page_one = client.get("/donors/?page=1").get_data(as_text=True)
    page_two = client.get("/donors/?page=2").get_data(as_text=True)

    assert "Donor Three" in page_one
    assert "Donor Two" in page_one
    assert "Donor One" not in page_one
    assert "Donor One" in page_two
    assert "Donor Three" not in page_two
    assert "Page 1 of 2" in page_one
    assert "Page 2 of 2" in page_two
