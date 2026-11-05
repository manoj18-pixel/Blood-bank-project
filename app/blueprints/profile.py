"""Profile, availability and password settings."""

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms import PasswordForm, ProfileForm
from app.utils.time import utcnow

bp = Blueprint("profile", __name__)


def _apply_profile(form: ProfileForm) -> None:
    for name in (
        "full_name",
        "phone",
        "blood_group",
        "date_of_birth",
        "gender",
        "city",
        "area",
        "pincode",
        "last_donation_date",
    ):
        setattr(current_user, name, getattr(form, name).data)
    current_user.area = (form.area.data or "").strip() or None
    current_user.pincode = (form.pincode.data or "").strip() or None
    current_user.gender = form.gender.data or None
    current_user.is_donor = form.is_donor.data
    current_user.is_available = form.is_available.data
    current_user.updated_at = utcnow()


@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    profile_form = ProfileForm(obj=current_user)
    password_form = PasswordForm()

    if profile_form.validate_on_submit():
        _apply_profile(profile_form)
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile.index"))

    return render_template(
        "profile/index.html",
        profile_form=profile_form,
        password_form=password_form,
        eligible=current_user.eligibility[0],
        reason=current_user.eligibility[1],
        eligible_from=current_user.eligible_from,
        cooldown_days_left=current_user.cooldown_days_left,
        donations=current_user.donations,
    )


@bp.post("/availability")
@login_required
def toggle_availability():
    current_user.is_available = not current_user.is_available
    current_user.updated_at = utcnow()
    db.session.commit()
    if current_user.is_available:
        flash("You are now marked available to donate.", "success")
    else:
        flash("You are now marked unavailable. You can switch back anytime.", "info")
    return redirect(url_for("profile.index"))


@bp.post("/password")
@login_required
def change_password():
    form = PasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Your current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash("Password changed successfully.", "success")
            return redirect(url_for("profile.index"))
    else:
        for errors in form.errors.values():
            for error in errors:
                flash(error, "danger")
    return redirect(url_for("profile.index"))
