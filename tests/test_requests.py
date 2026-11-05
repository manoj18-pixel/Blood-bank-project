"""Blood request tests (TC-REQ-*)."""

from datetime import date, timedelta

from app.extensions import db
from app.models import BloodRequest, Donation, DonorResponse
from app.utils.time import utcnow

REQUEST_DATA = {
    "patient_name": "Anita Test",
    "patient_age": 54,
    "blood_group": "A+",
    "units_needed": 2,
    "hospital_name": "Sassoon Hospital",
    "address": "Near station",
    "city": "Pune",
    "pincode": "411001",
    "urgency": "critical",
    "needed_by": "2030-01-01T10:00",
    "contact_phone": "9111111111",
    "notes": "Ward 4",
    "accept_terms": "y",
}


def test_create_request(client, make_user, login_as):
    requester = make_user(email="ravi@example.com", blood_group="A+", is_donor=False)
    login_as(client, requester.email)

    response = client.post("/requests/new", data=REQUEST_DATA, follow_redirects=False)

    assert response.status_code == 302
    blood_request = BloodRequest.query.filter_by(patient_name="Anita Test").first()
    assert blood_request is not None
    assert blood_request.requester_id == requester.id
    assert blood_request.status == "open"


def test_request_requires_future_needed_by(client, make_user, login_as):
    requester = make_user(email="ravi@example.com", is_donor=False)
    login_as(client, requester.email)
    payload = dict(REQUEST_DATA, needed_by="2000-01-01T10:00")

    response = client.post("/requests/new", data=payload)

    assert response.status_code == 200
    assert BloodRequest.query.count() == 0
    assert b"future" in response.data.lower()


def test_units_must_be_positive(client, make_user, login_as):
    requester = make_user(email="ravi@example.com", is_donor=False)
    login_as(client, requester.email)
    payload = dict(REQUEST_DATA, units_needed=0)

    response = client.post("/requests/new", data=payload)

    assert response.status_code == 200
    assert BloodRequest.query.count() == 0


def test_non_owner_cannot_edit_request(client, make_user, make_request, login_as):
    owner = make_user(email="owner@example.com", is_donor=False)
    other = make_user(email="other@example.com", is_donor=False)
    blood_request = make_request(owner)
    login_as(client, other.email)

    response = client.get(f"/requests/{blood_request.id}/edit")

    assert response.status_code == 403


def test_owner_can_edit_open_request(client, make_user, make_request, login_as):
    owner = make_user(email="owner@example.com", is_donor=False)
    blood_request = make_request(owner)
    login_as(client, owner.email)
    payload = dict(
        REQUEST_DATA,
        hospital_name="New Hospital",
        city=owner.city,
        needed_by="2030-02-01T10:00",
    )

    response = client.post(
        f"/requests/{blood_request.id}/edit", data=payload, follow_redirects=False
    )

    assert response.status_code == 302
    db.session.refresh(blood_request)
    assert blood_request.hospital_name == "New Hospital"


def test_owner_can_cancel_request(client, make_user, make_request, login_as):
    owner = make_user(email="owner@example.com", is_donor=False)
    blood_request = make_request(owner)
    login_as(client, owner.email)

    response = client.post(f"/requests/{blood_request.id}/cancel")

    assert response.status_code == 302
    db.session.refresh(blood_request)
    assert blood_request.status == "cancelled"


def test_expired_request_is_refreshed_on_read(client, make_user, make_request, login_as):
    owner = make_user(email="owner@example.com", is_donor=False)
    blood_request = make_request(owner, needed_by=utcnow() - timedelta(hours=2))
    login_as(client, owner.email)

    response = client.get(f"/requests/{blood_request.id}")

    assert response.status_code == 200
    db.session.refresh(blood_request)
    assert blood_request.status == "expired"


def test_fulfill_requires_matched_request(client, make_user, make_request, login_as):
    owner = make_user(email="owner@example.com", is_donor=False)
    blood_request = make_request(owner)
    login_as(client, owner.email)

    response = client.post(
        f"/requests/{blood_request.id}/fulfill",
        data={"donated_on": "2026-01-01", "units": 1},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert Donation.query.count() == 0
    assert b"matched" in response.data.lower()


def test_non_owner_cannot_fulfill(client, make_user, make_request, login_as):
    owner = make_user(email="owner@example.com", is_donor=False)
    other = make_user(email="other@example.com", is_donor=False)
    blood_request = make_request(owner)
    login_as(client, other.email)

    response = client.post(
        f"/requests/{blood_request.id}/fulfill",
        data={"donated_on": "2026-01-01", "units": 1},
    )

    assert response.status_code == 403


def test_missing_hospital_name_is_rejected(client, make_user, login_as):
    requester = make_user(email="ravi@example.com", is_donor=False)
    login_as(client, requester.email)
    payload = dict(REQUEST_DATA, hospital_name="")

    response = client.post("/requests/new", data=payload)

    assert response.status_code == 200
    assert BloodRequest.query.count() == 0


def test_request_notes_are_html_escaped(client, make_user, make_request, login_as):
    owner = make_user(email="owner@example.com", is_donor=False)
    blood_request = make_request(owner, notes="<script>alert('xss')</script>")
    login_as(client, owner.email)

    body = client.get(f"/requests/{blood_request.id}").get_data(as_text=True)

    assert "<script>alert('xss')</script>" not in body
    assert "&lt;script&gt;" in body


def test_cannot_edit_fulfilled_request(
    client, make_user, make_request, login_as
):
    owner = make_user(email="owner@example.com", is_donor=False)
    blood_request = make_request(owner, status="fulfilled")
    login_as(client, owner.email)

    response = client.post(
        f"/requests/{blood_request.id}/edit",
        data=dict(REQUEST_DATA, hospital_name="Changed Hospital"),
        follow_redirects=True,
    )

    assert response.status_code == 200
    db.session.refresh(blood_request)
    assert blood_request.hospital_name == "Test Hospital"
    assert b"Only open requests" in response.data


def test_fulfil_with_accepted_offer_records_donation(
    client, make_user, make_request, login_as
):
    owner = make_user(email="owner@example.com", is_donor=False)
    donor = make_user(email="donor@example.com", blood_group="O-")
    blood_request = make_request(owner, status="matched", blood_group="A+")
    offer = DonorResponse(
        request_id=blood_request.id, donor_id=donor.id, status="accepted"
    )
    db.session.add(offer)
    db.session.commit()
    login_as(client, owner.email)

    response = client.post(
        f"/requests/{blood_request.id}/fulfill",
        data={"donated_on": date.today().isoformat(), "units": 1},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Donation recorded" in response.data
    db.session.refresh(blood_request)
    db.session.refresh(donor)
    db.session.refresh(offer)
    assert blood_request.status == "fulfilled"
    assert offer.status == "donated"
    assert donor.is_available is False
    assert donor.last_donation_date == date.today()
    assert Donation.query.count() == 1


def test_fulfilling_twice_does_not_duplicate_donation(
    client, make_user, make_request, login_as
):
    owner = make_user(email="owner@example.com", is_donor=False)
    donor = make_user(email="donor@example.com", blood_group="O-")
    blood_request = make_request(owner, status="matched", blood_group="A+")
    offer = DonorResponse(
        request_id=blood_request.id, donor_id=donor.id, status="accepted"
    )
    db.session.add(offer)
    db.session.commit()
    login_as(client, owner.email)
    payload = {"donated_on": date.today().isoformat(), "units": 1}

    client.post(f"/requests/{blood_request.id}/fulfill", data=payload)
    response = client.post(
        f"/requests/{blood_request.id}/fulfill", data=payload, follow_redirects=True
    )

    assert response.status_code == 200
    assert Donation.query.count() == 1
    assert b"Only a matched request" in response.data
