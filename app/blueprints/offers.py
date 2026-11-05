"""Offer actions: send, accept, decline, withdraw."""

from flask import Blueprint, abort, flash, redirect, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms import OfferForm
from app.models import BloodRequest, DonorResponse
from app.services import requests as request_service

bp = Blueprint("offers", __name__)


@bp.post("/requests/<int:request_id>/offer")
@login_required
def create_offer(request_id):
    blood_request = db.get_or_404(BloodRequest, request_id)
    form = OfferForm()
    if not form.validate_on_submit():
        for errors in form.errors.values():
            for error in errors:
                flash(error, "danger")
        return redirect(url_for("requests.detail", request_id=blood_request.id))

    try:
        request_service.send_offer(blood_request, current_user, form.message.data)
    except request_service.WorkflowError as exc:
        flash(str(exc), "danger")
    else:
        flash(
            "Your offer has been sent. You will be notified when the requester responds.",
            "success",
        )
    return redirect(url_for("requests.detail", request_id=blood_request.id))


@bp.post("/offers/<int:offer_id>/accept")
@login_required
def accept(offer_id):
    offer = db.get_or_404(DonorResponse, offer_id)
    try:
        request_service.accept_offer(offer, current_user)
    except PermissionError:
        abort(403)
    except request_service.WorkflowError as exc:
        flash(str(exc), "danger")
    else:
        flash("Offer accepted. Contact details are now visible to both of you.", "success")
    return redirect(url_for("requests.detail", request_id=offer.request_id))


@bp.post("/offers/<int:offer_id>/decline")
@login_required
def decline(offer_id):
    offer = db.get_or_404(DonorResponse, offer_id)
    try:
        request_service.decline_offer(offer, current_user)
    except PermissionError:
        abort(403)
    except request_service.WorkflowError as exc:
        flash(str(exc), "danger")
    else:
        flash("Offer declined.", "info")
    return redirect(url_for("requests.detail", request_id=offer.request_id))


@bp.post("/offers/<int:offer_id>/withdraw")
@login_required
def withdraw(offer_id):
    offer = db.get_or_404(DonorResponse, offer_id)
    try:
        request_service.withdraw_offer(offer, current_user)
    except PermissionError:
        abort(403)
    except request_service.WorkflowError as exc:
        flash(str(exc), "danger")
    else:
        flash("Offer withdrawn.", "info")
    return redirect(url_for("requests.detail", request_id=offer.request_id))
