"""Request lifecycle rules and offer workflow.

Keeping transitions here (instead of in routes) means the same guards apply
to every caller and are easy to unit test.
"""

from datetime import date

from app.extensions import db
from app.models import BloodRequest, Donation, DonorResponse
from app.services.eligibility import eligibility, reason_label
from app.services.matching import donor_can_donate_to
from app.services.notifications import notify
from app.utils.time import utcnow


class WorkflowError(Exception):
    """A business-rule violation that should be shown to the user."""


def refresh_status(request: BloodRequest) -> bool:
    """Expire an open request whose needed_by time has passed."""
    if request.status == "open" and request.needed_by < utcnow():
        request.status = "expired"
        db.session.commit()
        return True
    return False


def can_edit(request: BloodRequest, user) -> bool:
    return request.requester_id == user.id and request.status == "open"


def has_offer(request: BloodRequest, donor) -> bool:
    return any(response.donor_id == donor.id for response in request.responses)


def send_offer(request: BloodRequest, donor, message: str | None = None) -> DonorResponse:
    if request.requester_id == donor.id:
        raise WorkflowError("You cannot offer to donate to your own request.")
    if request.status != "open":
        raise WorkflowError("This request is no longer accepting offers.")
    if request.needed_by < utcnow():
        raise WorkflowError("This request has expired.")
    if not donor_can_donate_to(donor.blood_group, request.blood_group):
        raise WorkflowError(
            "Your blood group is not compatible with this request."
        )
    ok, reason = eligibility(donor)
    if not ok:
        raise WorkflowError(f"You cannot donate right now: {reason_label(reason).lower()}.")
    if has_offer(request, donor):
        raise WorkflowError("You have already offered to help with this request.")

    response = DonorResponse(
        request_id=request.id,
        donor_id=donor.id,
        message=(message or "").strip() or None,
    )
    db.session.add(response)
    db.session.flush()
    notify(
        request.requester_id,
        "offer_received",
        "New donor offer",
        f"{donor.full_name} ({donor.blood_group}) offered to help with the request for "
        f"{request.patient_name}.",
        link=f"/requests/{request.id}",
        commit=False,
    )
    db.session.commit()
    return response


def _owned_offer(offer: DonorResponse, actor) -> BloodRequest:
    request = offer.request
    if request.requester_id != actor.id:
        raise PermissionError("Only the request owner can manage offers.")
    return request


def accept_offer(offer: DonorResponse, actor) -> None:
    request = _owned_offer(offer, actor)
    if request.status != "open":
        raise WorkflowError("Only an open request can accept an offer.")
    if offer.status != "offered":
        raise WorkflowError("This offer is no longer available.")

    offer.status = "accepted"
    request.status = "matched"
    notify(
        offer.donor_id,
        "offer_accepted",
        "Your offer was accepted",
        f"{actor.full_name} accepted your offer for {request.patient_name}. "
        f"Contact them on {request.contact_phone}.",
        link=f"/requests/{request.id}",
        commit=False,
    )
    db.session.commit()


def decline_offer(offer: DonorResponse, actor) -> None:
    request = _owned_offer(offer, actor)
    if offer.status != "offered":
        raise WorkflowError("This offer can no longer be declined.")
    offer.status = "declined"
    notify(
        offer.donor_id,
        "offer_declined",
        "Offer declined",
        f"Your offer for {request.patient_name} was declined. Thank you for stepping up.",
        link=f"/requests/{request.id}",
        commit=False,
    )
    db.session.commit()


def withdraw_offer(offer: DonorResponse, actor) -> None:
    if offer.donor_id != actor.id:
        raise PermissionError("You can only withdraw your own offer.")
    if offer.status != "offered":
        raise WorkflowError("This offer can no longer be withdrawn.")
    offer.status = "withdrawn"
    request = offer.request
    notify(
        request.requester_id,
        "offer_withdrawn",
        "Donor withdrew an offer",
        f"{actor.full_name} withdrew their offer for {request.patient_name}.",
        link=f"/requests/{request.id}",
        commit=False,
    )
    db.session.commit()


def fulfill_request(
    request: BloodRequest,
    actor,
    donated_on: date,
    units: int = 1,
    notes: str | None = None,
) -> Donation:
    if request.requester_id != actor.id:
        raise PermissionError("Only the request owner can mark it fulfilled.")
    if request.status != "matched":
        raise WorkflowError("Only a matched request can be marked fulfilled.")
    response = request.accepted_response
    if response is None:
        raise WorkflowError("An accepted donor is required before fulfilling.")

    donor = response.donor
    donation = Donation(
        donor_id=donor.id,
        request_id=request.id,
        hospital_name=request.hospital_name,
        donated_on=donated_on,
        units=units,
        notes=(notes or "").strip() or None,
        verified_by=actor.id,
    )
    response.status = "donated"
    request.status = "fulfilled"
    request.fulfilled_at = utcnow()
    donor.last_donation_date = donated_on
    donor.is_available = False

    db.session.add(donation)
    db.session.flush()
    notify(
        donor.id,
        "request_fulfilled",
        "Thank you for donating",
        f"Your donation for {request.patient_name} has been recorded. "
        "You will be eligible again after the cooldown period.",
        link=f"/requests/{request.id}",
        commit=False,
    )
    db.session.commit()
    return donation


def cancel_request(request: BloodRequest, actor) -> None:
    if request.requester_id != actor.id:
        raise PermissionError("Only the request owner can cancel it.")
    if request.status not in {"open", "matched"}:
        raise WorkflowError("This request can no longer be cancelled.")
    accepted = request.accepted_response
    request.status = "cancelled"
    if accepted and accepted.status == "accepted":
        accepted.status = "withdrawn"
        notify(
            accepted.donor_id,
            "request_cancelled",
            "Request cancelled",
            f"The request for {request.patient_name} was cancelled by the requester.",
            link=f"/requests/{request.id}",
            commit=False,
        )
    db.session.commit()


def donor_contact_for(request: BloodRequest, viewer):
    """Full donor record only for the request owner after acceptance."""
    if not viewer or not getattr(viewer, "is_authenticated", False):
        return None
    if request.requester_id != viewer.id:
        return None
    accepted = request.accepted_response
    return accepted.donor if accepted else None


def requester_contact_for(request: BloodRequest, viewer):
    """Requester record only for a donor whose offer was accepted."""
    if not viewer or not getattr(viewer, "is_authenticated", False):
        return None
    for response in request.responses:
        if response.donor_id == viewer.id and response.status in {"accepted", "donated"}:
            return request.requester
    return None
