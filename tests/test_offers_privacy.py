"""Offer workflow and contact privacy tests (TC-OFF-*)."""

from datetime import date

from app.extensions import db
from app.models import Donation, DonorResponse, Notification


def offer_payload(message="Available this evening"):
    return {"message": message}


def test_offer_creates_notification_and_is_hidden_before_accept(
    app, make_user, make_request, login_as
):
    requester = make_user(
        email="ravi@example.com", phone="9333333333", blood_group="A+", is_donor=False
    )
    donor = make_user(
        email="asha@example.com",
        phone="9222222222",
        blood_group="O-",
        city="Pune",
    )
    blood_request = make_request(
        requester, contact_phone="9444444444", blood_group="A+"
    )

    donor_client = app.test_client()
    login_as(donor_client, donor.email)
    response = donor_client.post(
        f"/requests/{blood_request.id}/offer", data=offer_payload()
    )
    assert response.status_code == 302

    offer = DonorResponse.query.filter_by(request_id=blood_request.id).first()
    assert offer is not None
    assert offer.status == "offered"
    assert Notification.query.filter_by(user_id=requester.id).count() == 1

    requester_client = app.test_client()
    login_as(requester_client, requester.email)
    page = requester_client.get(f"/requests/{blood_request.id}").get_data(as_text=True)

    assert donor.phone not in page
    assert donor.masked_phone in page


def test_accept_reveals_contact_to_both_sides(
    app, make_user, make_request, login_as
):
    requester = make_user(
        email="ravi@example.com", phone="9333333333", blood_group="A+", is_donor=False
    )
    donor = make_user(
        email="asha@example.com", phone="9222222222", blood_group="O-", city="Pune"
    )
    blood_request = make_request(
        requester, contact_phone="9444444444", blood_group="A+"
    )
    offer = DonorResponse(
        request_id=blood_request.id, donor_id=donor.id, status="offered"
    )
    db.session.add(offer)
    db.session.commit()

    requester_client = app.test_client()
    login_as(requester_client, requester.email)
    response = requester_client.post(f"/offers/{offer.id}/accept")
    assert response.status_code == 302

    db.session.refresh(offer)
    db.session.refresh(blood_request)
    assert offer.status == "accepted"
    assert blood_request.status == "matched"

    page = requester_client.get(f"/requests/{blood_request.id}").get_data(as_text=True)
    assert donor.phone in page

    donor_client = app.test_client()
    login_as(donor_client, donor.email)
    donor_page = donor_client.get(f"/requests/{blood_request.id}").get_data(as_text=True)
    assert blood_request.contact_phone in donor_page


def test_non_owner_cannot_accept_offer(app, make_user, make_request, login_as):
    owner = make_user(email="owner@example.com", is_donor=False)
    other = make_user(email="other@example.com", is_donor=False)
    donor = make_user(email="donor@example.com")
    blood_request = make_request(owner)
    offer = DonorResponse(
        request_id=blood_request.id, donor_id=donor.id, status="offered"
    )
    db.session.add(offer)
    db.session.commit()

    other_client = app.test_client()
    login_as(other_client, other.email)
    response = other_client.post(f"/offers/{offer.id}/accept")

    assert response.status_code == 403


def test_ineligible_donor_cannot_offer(
    app, make_user, make_request, login_as
):
    requester = make_user(email="ravi@example.com", blood_group="A+", is_donor=False)
    donor = make_user(
        email="asha@example.com", blood_group="O-", last_donation_date=date.today()
    )
    blood_request = make_request(requester, blood_group="A+")
    donor_client = app.test_client()
    login_as(donor_client, donor.email)

    response = donor_client.post(
        f"/requests/{blood_request.id}/offer",
        data=offer_payload(),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert DonorResponse.query.count() == 0
    assert b"cannot donate" in response.data.lower()


def test_duplicate_offer_is_blocked(
    app, make_user, make_request, login_as
):
    requester = make_user(email="ravi@example.com", blood_group="A+", is_donor=False)
    donor = make_user(email="asha@example.com", blood_group="O-")
    blood_request = make_request(requester, blood_group="A+")
    donor_client = app.test_client()
    login_as(donor_client, donor.email)

    donor_client.post(f"/requests/{blood_request.id}/offer", data=offer_payload())
    response = donor_client.post(
        f"/requests/{blood_request.id}/offer",
        data=offer_payload(),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert DonorResponse.query.count() == 1
    assert b"already offered" in response.data.lower()


def test_incompatible_donor_cannot_offer(
    app, make_user, make_request, login_as
):
    requester = make_user(email="ravi@example.com", blood_group="A+", is_donor=False)
    donor = make_user(email="asha@example.com", blood_group="B+")
    blood_request = make_request(requester, blood_group="A+")
    donor_client = app.test_client()
    login_as(donor_client, donor.email)

    response = donor_client.post(
        f"/requests/{blood_request.id}/offer",
        data=offer_payload(),
        follow_redirects=True,
    )

    assert Donation.query.count() == 0
    assert DonorResponse.query.count() == 0
    assert b"not compatible" in response.data.lower()


def test_requester_cannot_offer_on_own_request(
    app, make_user, make_request, login_as
):
    requester = make_user(
        email="ravi@example.com", blood_group="A+", is_donor=True
    )
    blood_request = make_request(requester, blood_group="A+")
    client = app.test_client()
    login_as(client, requester.email)

    response = client.post(
        f"/requests/{blood_request.id}/offer",
        data=offer_payload(),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert DonorResponse.query.count() == 0
    assert b"own request" in response.data.lower()


def test_decline_keeps_phone_hidden(
    app, make_user, make_request, login_as
):
    requester = make_user(
        email="ravi@example.com", blood_group="A+", is_donor=False
    )
    donor = make_user(
        email="asha@example.com", phone="9222222222", blood_group="O-"
    )
    blood_request = make_request(requester)
    offer = DonorResponse(
        request_id=blood_request.id, donor_id=donor.id, status="offered"
    )
    db.session.add(offer)
    db.session.commit()
    client = app.test_client()
    login_as(client, requester.email)

    response = client.post(f"/offers/{offer.id}/decline", follow_redirects=True)

    assert response.status_code == 200
    db.session.refresh(offer)
    assert offer.status == "declined"
    assert donor.phone not in response.get_data(as_text=True)
    assert Notification.query.filter_by(user_id=donor.id).count() == 1


def test_donor_can_withdraw_offer(app, make_user, make_request, login_as):
    requester = make_user(
        email="ravi@example.com", blood_group="A+", is_donor=False
    )
    donor = make_user(email="asha@example.com", blood_group="O-")
    blood_request = make_request(requester)
    offer = DonorResponse(
        request_id=blood_request.id, donor_id=donor.id, status="offered"
    )
    db.session.add(offer)
    db.session.commit()
    client = app.test_client()
    login_as(client, donor.email)

    response = client.post(f"/offers/{offer.id}/withdraw", follow_redirects=True)

    assert response.status_code == 200
    db.session.refresh(offer)
    assert offer.status == "withdrawn"
    assert Notification.query.filter_by(user_id=requester.id).count() == 1


def test_second_offer_after_acceptance_is_blocked(
    app, make_user, make_request, login_as
):
    requester = make_user(
        email="ravi@example.com", blood_group="A+", is_donor=False
    )
    first_donor = make_user(email="first@example.com", blood_group="O-")
    second_donor = make_user(email="second@example.com", blood_group="O-")
    blood_request = make_request(requester)
    offer = DonorResponse(
        request_id=blood_request.id, donor_id=first_donor.id, status="offered"
    )
    db.session.add(offer)
    db.session.commit()

    owner_client = app.test_client()
    login_as(owner_client, requester.email)
    owner_client.post(f"/offers/{offer.id}/accept")

    donor_client = app.test_client()
    login_as(donor_client, second_donor.email)
    response = donor_client.post(
        f"/requests/{blood_request.id}/offer",
        data=offer_payload(),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert DonorResponse.query.count() == 1
    assert b"no longer accepting offers" in response.data.lower()
