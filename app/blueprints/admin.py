"""Administrator console."""

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
from flask_login import current_user
from sqlalchemy import or_

from app.constants import REQUEST_STATUSES
from app.extensions import db
from app.models import AuditLog, BloodRequest, Donation, DonorResponse, User
from app.services.audit import log_action
from app.services.notifications import notify
from app.utils.decorators import admin_required
from app.utils.time import utcnow

bp = Blueprint("admin", __name__)


@bp.get("/")
@admin_required
def index():
    stats = {
        "users": User.query.count(),
        "donors": User.query.filter(User.is_donor.is_(True)).count(),
        "open_requests": BloodRequest.query.filter_by(status="open").count(),
        "matched_requests": BloodRequest.query.filter_by(status="matched").count(),
        "fulfilled": BloodRequest.query.filter_by(status="fulfilled").count(),
        "donations": Donation.query.count(),
    }
    stats["fulfilment_rate"] = (
        round(stats["fulfilled"] * 100 / stats["donations"], 1)
        if stats["donations"]
        else 0
    )
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_requests = (
        BloodRequest.query.order_by(BloodRequest.created_at.desc()).limit(5).all()
    )
    recent_audit = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()
    return render_template(
        "admin/index.html",
        stats=stats,
        recent_users=recent_users,
        recent_requests=recent_requests,
        recent_audit=recent_audit,
    )


@bp.get("/users")
@admin_required
def users():
    search = (request.args.get("q") or "").strip()
    page = request.args.get("page", 1, type=int)
    query = User.query
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(
            or_(
                User.full_name.ilike(like),
                User.email.ilike(like),
                User.city.ilike(like),
            )
        )
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=current_app.config["PER_PAGE"], error_out=False
    )
    return render_template(
        "admin/users.html", pagination=pagination, search=search
    )


@bp.post("/users/<int:user_id>/suspend")
@admin_required
def suspend_user(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("You cannot suspend your own account.", "danger")
        return redirect(url_for("admin.users"))

    if user.status == "suspended":
        user.status = "active"
        action = "reactivate_user"
        flash(f"{user.full_name} has been reactivated.", "success")
    else:
        user.status = "suspended"
        action = "suspend_user"
        # A suspended donor can no longer fulfil their outstanding offers, so
        # withdraw them and let the affected requesters know.
        open_offers = DonorResponse.query.filter_by(
            donor_id=user.id, status="offered"
        ).all()
        for offer in open_offers:
            offer.status = "withdrawn"
            notify(
                offer.request.requester_id,
                "offer_withdrawn",
                "Donor offer withdrawn",
                f"{user.full_name} is no longer available to help with the "
                f"request for {offer.request.patient_name}.",
                link=f"/requests/{offer.request_id}",
                commit=False,
            )
        flash(f"{user.full_name} has been suspended.", "info")

    db.session.flush()
    log_action(current_user.id, action, f"user:{user.id}", user.email)
    notify(
        user.id,
        "account_status",
        "Account status updated",
        "Your account status was updated by an administrator. "
        "Please contact support if you have questions.",
        link=None,
        commit=True,
    )
    return redirect(url_for("admin.users"))


@bp.post("/users/<int:user_id>/verify")
@admin_required
def verify_user(user_id):
    user = db.get_or_404(User, user_id)
    user.email_verified = True
    db.session.flush()
    log_action(current_user.id, "verify_user", f"user:{user.id}", user.email)
    flash(f"{user.full_name}'s email has been marked verified.", "success")
    return redirect(url_for("admin.users"))


@bp.get("/requests")
@admin_required
def requests():
    status = (request.args.get("status") or "").strip()
    page = request.args.get("page", 1, type=int)
    query = BloodRequest.query
    if status in REQUEST_STATUSES:
        query = query.filter(BloodRequest.status == status)
    pagination = query.order_by(BloodRequest.created_at.desc()).paginate(
        page=page, per_page=current_app.config["PER_PAGE"], error_out=False
    )
    return render_template(
        "admin/requests.html",
        pagination=pagination,
        status=status,
    )


@bp.post("/requests/<int:request_id>/remove")
@admin_required
def remove_request(request_id):
    blood_request = db.get_or_404(BloodRequest, request_id)
    if blood_request.status not in {"open", "matched"}:
        flash("Only open or matched requests can be removed.", "warning")
        return redirect(url_for("admin.requests"))

    blood_request.status = "cancelled"
    db.session.flush()
    log_action(
        current_user.id,
        "remove_request",
        f"request:{blood_request.id}",
        f"{blood_request.blood_group} {blood_request.city}",
    )
    notify(
        blood_request.requester_id,
        "request_removed",
        "Request removed",
        f"Your request for {blood_request.patient_name} was removed by an administrator.",
        link=f"/requests/{blood_request.id}",
        commit=True,
    )
    flash("Request removed.", "success")
    return redirect(url_for("admin.requests"))
