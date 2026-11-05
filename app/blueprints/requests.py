"""Blood request pages and actions."""

from datetime import timedelta

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import case, func

from app.constants import BLOOD_GROUPS, REQUEST_STATUSES, URGENCY_LEVELS
from app.extensions import db
from app.forms import FulfillForm, OfferForm, RequestForm
from app.models import BloodRequest, DonorResponse
from app.services import requests as request_service
from app.services.eligibility import eligibility, reason_label
from app.services.matching import (
    compatible_recipient_groups,
    donor_can_donate_to,
    find_matching_donors,
)
from app.utils.time import utcnow

bp = Blueprint("requests", __name__)


def _apply_form(blood_request: BloodRequest, form: RequestForm) -> None:
    for name in (
        "patient_name",
        "patient_age",
        "blood_group",
        "units_needed",
        "hospital_name",
        "address",
        "city",
        "pincode",
        "urgency",
        "needed_by",
        "contact_phone",
    ):
        setattr(blood_request, name, getattr(form, name).data)
    blood_request.notes = (form.notes.data or "").strip() or None


@bp.get("/")
@login_required
def index():
    status = (request.args.get("status") or "open").strip()
    blood_group = (request.args.get("group") or "").strip()
    city = (request.args.get("city") or "").strip()
    urgency = (request.args.get("urgency") or "").strip()
    mine = request.args.get("mine") == "1"
    page = request.args.get("page", 1, type=int)

    query = BloodRequest.query
    if status in REQUEST_STATUSES:
        query = query.filter(BloodRequest.status == status)
    if status == "open":
        query = query.filter(BloodRequest.needed_by > utcnow())
    if blood_group in BLOOD_GROUPS:
        query = query.filter(BloodRequest.blood_group == blood_group)
    if city:
        query = query.filter(func.lower(BloodRequest.city) == city.lower())
    if urgency in URGENCY_LEVELS:
        query = query.filter(BloodRequest.urgency == urgency)
    if mine and current_user.is_donor:
        query = query.filter(
            BloodRequest.blood_group.in_(
                compatible_recipient_groups(current_user.blood_group)
            )
        )

    urgency_order = case(
        {"critical": 0, "urgent": 1, "normal": 2},
        value=BloodRequest.urgency,
        else_=3,
    )
    pagination = query.order_by(urgency_order, BloodRequest.needed_by.asc()).paginate(
        page=page, per_page=current_app.config["PER_PAGE"], error_out=False
    )

    offered_ids = {
        response.request_id
        for response in DonorResponse.query.filter_by(donor_id=current_user.id).all()
    }

    return render_template(
        "requests/index.html",
        pagination=pagination,
        status=status,
        blood_group=blood_group,
        city=city,
        urgency=urgency,
        mine=mine,
        offered_ids=offered_ids,
    )


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = RequestForm()
    if request.method == "GET":
        form.contact_phone.data = current_user.phone
        form.city.data = current_user.city
        form.needed_by.data = (utcnow() + timedelta(days=1)).replace(
            minute=0, second=0, microsecond=0
        )

    if form.validate_on_submit():
        blood_request = BloodRequest(requester_id=current_user.id, status="open")
        _apply_form(blood_request, form)
        db.session.add(blood_request)
        db.session.commit()
        flash("Your blood request is live. Compatible donors can now offer to help.", "success")
        return redirect(url_for("requests.detail", request_id=blood_request.id))

    return render_template("requests/form.html", form=form, mode="new")


@bp.get("/<int:request_id>")
@login_required
def detail(request_id):
    blood_request = db.get_or_404(BloodRequest, request_id)
    request_service.refresh_status(blood_request)

    is_owner = blood_request.requester_id == current_user.id
    my_offer = next(
        (r for r in blood_request.responses if r.donor_id == current_user.id), None
    )
    eligible_now, eligibility_reason = eligibility(current_user)

    matching = []
    if is_owner and blood_request.status in {"open", "matched"}:
        matching = find_matching_donors(blood_request)

    can_offer = (
        blood_request.status == "open"
        and not is_owner
        and current_user.is_donor
        and donor_can_donate_to(current_user.blood_group, blood_request.blood_group)
        and my_offer is None
        and eligible_now
    )

    accepted_donor = request_service.donor_contact_for(blood_request, current_user)
    requester_contact = request_service.requester_contact_for(blood_request, current_user)

    return render_template(
        "requests/detail.html",
        blood_request=blood_request,
        is_owner=is_owner,
        my_offer=my_offer,
        matching=matching,
        can_offer=can_offer,
        eligible_now=eligible_now,
        eligibility_reason=eligibility_reason,
        eligibility_label=reason_label(eligibility_reason),
        accepted_donor=accepted_donor,
        requester_contact=requester_contact,
        offer_form=OfferForm(),
        fulfill_form=FulfillForm(),
    )


@bp.route("/<int:request_id>/edit", methods=["GET", "POST"])
@login_required
def edit(request_id):
    blood_request = db.get_or_404(BloodRequest, request_id)
    if blood_request.requester_id != current_user.id:
        abort(403)
    if not request_service.can_edit(blood_request, current_user):
        flash("Only open requests can be edited.", "warning")
        return redirect(url_for("requests.detail", request_id=blood_request.id))

    form = RequestForm(obj=blood_request)
    if request.method == "GET":
        form.needed_by.data = blood_request.needed_by
        form.accept_terms.data = True

    if form.validate_on_submit():
        _apply_form(blood_request, form)
        db.session.commit()
        flash("Request updated.", "success")
        return redirect(url_for("requests.detail", request_id=blood_request.id))

    return render_template(
        "requests/form.html", form=form, mode="edit", blood_request=blood_request
    )


@bp.post("/<int:request_id>/cancel")
@login_required
def cancel(request_id):
    blood_request = db.get_or_404(BloodRequest, request_id)
    try:
        request_service.cancel_request(blood_request, current_user)
    except PermissionError:
        abort(403)
    except request_service.WorkflowError as exc:
        flash(str(exc), "danger")
    else:
        flash("Request cancelled.", "info")
    return redirect(url_for("requests.detail", request_id=blood_request.id))


@bp.post("/<int:request_id>/fulfill")
@login_required
def fulfill(request_id):
    blood_request = db.get_or_404(BloodRequest, request_id)
    if blood_request.requester_id != current_user.id:
        abort(403)

    form = FulfillForm()
    if form.validate_on_submit():
        if form.units.data > blood_request.units_needed:
            flash("Units donated cannot exceed the units requested.", "danger")
        else:
            try:
                request_service.fulfill_request(
                    blood_request,
                    current_user,
                    donated_on=form.donated_on.data,
                    units=form.units.data,
                    notes=form.notes.data,
                )
            except request_service.WorkflowError as exc:
                flash(str(exc), "danger")
            else:
                flash("Donation recorded. The request is now fulfilled.", "success")
    else:
        for errors in form.errors.values():
            for error in errors:
                flash(error, "danger")

    return redirect(url_for("requests.detail", request_id=blood_request.id))
