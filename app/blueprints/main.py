"""Landing page, dashboard and public JSON stats."""

from flask import Blueprint, jsonify, render_template
from flask_login import current_user, login_required

from app.extensions import db
from app.models import BloodRequest, Donation, DonorResponse, User
from app.services.eligibility import eligibility, reason_label
from app.services.matching import matching_requests_for_donor
from app.utils.time import utcnow

bp = Blueprint("main", __name__)


def platform_stats() -> dict:
    return {
        "users": User.query.count(),
        "donors": User.query.filter(
            User.is_donor.is_(True), User.status == "active"
        ).count(),
        "open_requests": BloodRequest.query.filter(
            BloodRequest.status == "open", BloodRequest.needed_by > utcnow()
        ).count(),
        "donations": Donation.query.count(),
        "fulfilled": BloodRequest.query.filter_by(status="fulfilled").count(),
    }


@bp.get("/")
def index():
    stats = platform_stats()
    recent_requests = (
        BloodRequest.query.filter(
            BloodRequest.status == "open",
            BloodRequest.needed_by > utcnow(),
        )
        .order_by(BloodRequest.urgency.desc(), BloodRequest.needed_by.asc())
        .limit(3)
        .all()
    )
    return render_template("main/index.html", stats=stats, recent_requests=recent_requests)


@bp.get("/dashboard")
@login_required
def dashboard():
    my_requests = (
        BloodRequest.query.filter(
            BloodRequest.requester_id == current_user.id,
            BloodRequest.status.in_(["open", "matched"]),
        )
        .order_by(BloodRequest.created_at.desc())
        .limit(5)
        .all()
    )

    offers_received = (
        DonorResponse.query.join(BloodRequest)
        .filter(
            BloodRequest.requester_id == current_user.id,
            DonorResponse.status == "offered",
        )
        .order_by(DonorResponse.created_at.desc())
        .limit(6)
        .all()
    )

    my_offers = (
        DonorResponse.query.filter_by(donor_id=current_user.id)
        .order_by(DonorResponse.created_at.desc())
        .limit(5)
        .all()
    )

    nearby_requests = []
    if current_user.is_donor:
        nearby_requests = matching_requests_for_donor(current_user, limit=6)

    eligible, reason = eligibility(current_user)

    return render_template(
        "main/dashboard.html",
        my_requests=my_requests,
        offers_received=offers_received,
        my_offers=my_offers,
        nearby_requests=nearby_requests,
        eligible=eligible,
        eligibility_reason=reason,
        eligibility_label=reason_label(reason),
        my_donations=current_user.donations[:5],
        stats=platform_stats(),
    )


@bp.get("/my-donations")
@login_required
def my_donations():
    return render_template("main/my_donations.html", donations=current_user.donations)


@bp.get("/api/stats")
def api_stats():
    return jsonify(platform_stats())
