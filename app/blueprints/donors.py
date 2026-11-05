"""Donor directory, donor profile and JSON search API."""

from datetime import date, timedelta

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import case, func, or_

from app.constants import BLOOD_GROUPS
from app.extensions import db
from app.models import User
from app.services.eligibility import eligibility, reason_label
from app.services.matching import compatible_donor_groups, compatible_recipient_groups

bp = Blueprint("donors", __name__)


def _donor_query(recipient_group: str, city: str, include_unavailable: bool):
    query = User.query.filter(User.is_donor.is_(True), User.status == "active")

    if recipient_group in BLOOD_GROUPS:
        query = query.filter(
            User.blood_group.in_(compatible_donor_groups(recipient_group))
        )
    if city:
        query = query.filter(func.lower(User.city) == city.strip().lower())

    if not include_unavailable:
        query = query.filter(User.is_available.is_(True))
        cooldown = int(current_app.config["DONATION_COOLDOWN_DAYS"])
        cutoff = date.today() - timedelta(days=cooldown)
        query = query.filter(
            or_(User.last_donation_date.is_(None), User.last_donation_date <= cutoff)
        )
    return query


def _ordered(query):
    return query.order_by(
        User.is_available.desc(),
        case((User.last_donation_date.is_(None), 0), else_=1),
        User.last_donation_date.asc(),
        User.id.desc(),
    )


@bp.get("/")
@login_required
def index():
    recipient_group = (request.args.get("group") or "").strip()
    city = (request.args.get("city") or "").strip()
    include_unavailable = request.args.get("include_unavailable") == "1"
    page = request.args.get("page", 1, type=int)

    query = _donor_query(recipient_group, city, include_unavailable)
    pagination = _ordered(query).paginate(
        page=page, per_page=current_app.config["PER_PAGE"], error_out=False
    )

    rows = []
    for donor in pagination.items:
        ok, reason = eligibility(donor)
        rows.append(
            {
                "donor": donor,
                "eligible": ok,
                "reason": reason,
                "reason_label": reason_label(reason),
            }
        )

    return render_template(
        "donors/index.html",
        rows=rows,
        pagination=pagination,
        recipient_group=recipient_group,
        city=city,
        include_unavailable=include_unavailable,
        compatible_groups=(
            compatible_donor_groups(recipient_group)
            if recipient_group in BLOOD_GROUPS
            else []
        ),
    )


@bp.get("/<int:donor_id>")
@login_required
def show(donor_id):
    donor = db.get_or_404(User, donor_id)
    if not donor.is_donor or donor.status != "active":
        return render_template("errors/404.html"), 404

    ok, reason = eligibility(donor)
    return render_template(
        "donors/show.html",
        donor=donor,
        eligible=ok,
        reason=reason,
        reason_label=reason_label(reason),
        can_give_to=compatible_recipient_groups(donor.blood_group),
        is_self=donor.id == current_user.id,
    )


@bp.get("/api/search")
@login_required
def api_search():
    recipient_group = (request.args.get("group") or "").strip()
    city = (request.args.get("city") or "").strip()
    include_unavailable = request.args.get("include_unavailable") == "1"
    page = request.args.get("page", 1, type=int)

    query = _donor_query(recipient_group, city, include_unavailable)
    pagination = _ordered(query).paginate(
        page=page, per_page=current_app.config["PER_PAGE"], error_out=False
    )
    return jsonify(
        {
            "items": [donor.to_public_dict() for donor in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
        }
    )
