"""In-app notification inbox."""

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Notification
from app.utils.urls import is_safe_url

bp = Blueprint("notifications", __name__)


@bp.get("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    pagination = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .paginate(
            page=page, per_page=current_app.config["PER_PAGE"], error_out=False
        )
    )
    return render_template("notifications/index.html", pagination=pagination)


@bp.post("/<int:notification_id>/read")
@login_required
def mark_read(notification_id):
    notification = db.get_or_404(Notification, notification_id)
    if notification.user_id != current_user.id:
        abort(403)
    notification.is_read = True
    db.session.commit()
    target = notification.link if is_safe_url(notification.link) else None
    return redirect(target or url_for("notifications.index"))


@bp.post("/read-all")
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update(
        {"is_read": True}
    )
    db.session.commit()
    return redirect(url_for("notifications.index"))


@bp.get("/api/unread-count")
@login_required
def unread_count():
    count = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).count()
    return jsonify({"count": count})
