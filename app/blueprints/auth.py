"""Authentication routes: register, login, logout, verification, reset."""

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func

from app.extensions import db, limiter
from app.forms import ForgotForm, LoginForm, RegisterForm, ResetForm
from app.models import User
from app.services.mailer import send_email
from app.services.tokens import consume_token, create_token, peek_token
from app.utils.urls import is_safe_url

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("20 per hour", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter(func.lower(User.email) == email).first():
            form.email.errors.append("An account with this email already exists.")
        else:
            user = User(
                full_name=form.full_name.data.strip(),
                email=email,
                phone=form.phone.data.strip(),
                blood_group=form.blood_group.data,
                city=form.city.data.strip(),
                area=(form.area.data or "").strip() or None,
                pincode=(form.pincode.data or "").strip() or None,
                email_verified=not current_app.config["REQUIRE_EMAIL_VERIFICATION"],
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()

            if not user.email_verified:
                raw = create_token(user, "verify_email", expires_minutes=60 * 24)
                link = url_for("auth.verify_email", token=raw, _external=True)
                send_email(
                    "Verify your BloodLink email",
                    [user.email],
                    f"Welcome to BloodLink!\n\nVerify your email: {link}",
                )
                if current_app.debug:
                    flash(f"Development verification link: {link}", "info")

            login_user(user)
            flash(f"Welcome to BloodLink, {user.full_name.split()[0]}!", "success")
            return redirect(url_for("main.dashboard"))

    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter(func.lower(User.email) == email).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("This account is suspended. Please contact an administrator.", "danger")
            else:
                login_user(user, remember=form.remember.data)
                flash("Signed in successfully.", "success")
                next_page = request.args.get("next")
                if not is_safe_url(next_page):
                    next_page = None
                return redirect(next_page or url_for("main.dashboard"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.index"))


@bp.get("/verify/<token>")
def verify_email(token):
    user = consume_token(token, "verify_email")
    if not user:
        flash("This verification link is invalid or has expired.", "danger")
        return redirect(url_for("auth.login"))

    user.email_verified = True
    db.session.commit()
    flash("Your email is verified. Thank you!", "success")
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@bp.route("/forgot", methods=["GET", "POST"])
@limiter.limit("5 per 15 minutes", methods=["POST"])
def forgot_password():
    form = ForgotForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter(func.lower(User.email) == email).first()
        if user and user.is_active:
            raw = create_token(user, "reset_password", expires_minutes=60)
            link = url_for("auth.reset_password", token=raw, _external=True)
            send_email(
                "Reset your BloodLink password",
                [user.email],
                f"Use this link within 60 minutes to reset your password: {link}",
            )
            if current_app.debug:
                flash(f"Development reset link: {link}", "info")
        flash("If that email is registered, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot.html", form=form)


@bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    if not peek_token(token, "reset_password"):
        flash("This reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetForm()
    if form.validate_on_submit():
        user = consume_token(token, "reset_password")
        if not user:
            flash("This reset link is invalid or has expired.", "danger")
            return redirect(url_for("auth.forgot_password"))
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been updated. Please sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset.html", form=form, token=token)
