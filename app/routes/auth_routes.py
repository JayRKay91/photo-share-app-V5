from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import SignatureExpired, BadSignature

from app.extensions import db
from app.models import User
from app.email.utils import send_verification_email, send_password_reset_email
from app.utils.token_utils import get_token_serializer

auth_bp = Blueprint('auth', __name__)

# ──────────────────────────────────────────────────────────────────────────────
# 📋 REGISTER: Create new user, then send verification email
# ──────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        confirm = request.form.get("confirm_password", "").strip()

        if password != confirm:
            flash("Passwords do not match", "error")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(username=username).first():
            flash("Username already taken", "error")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("Email already in use", "error")
            return redirect(url_for("auth.register"))

        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_verified=False
        )
        db.session.add(new_user)
        db.session.commit()

        send_verification_email(new_user)

        flash("Account created! Please verify your email before logging in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# ──────────────────────────────────────────────────────────────────────────────
# 🔐 LOGIN: Allow only verified users to log in
# ──────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            if not user.is_verified:
                flash("Please verify your email before logging in.", "warning")
                return redirect(url_for("auth.login"))

            login_user(user, remember=True)
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(request.args.get("next") or url_for("gallery.index"))
        else:
            flash("Invalid username or password", "error")

    return render_template("auth/login.html")


# ──────────────────────────────────────────────────────────────────────────────
# 🔓 LOGOUT
# ──────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You’ve been logged out.", "info")
    return redirect(url_for("auth.login"))


# ──────────────────────────────────────────────────────────────────────────────
# 📧 VERIFY: Activate user account from email link
# ──────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/verify/<token>")
def verify_token(token):
    try:
        email = get_token_serializer().loads(token, max_age=3600)
    except SignatureExpired:
        flash("Verification link expired.", "error")
        return redirect(url_for("auth.login"))
    except BadSignature:
        flash("Invalid verification link.", "error")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("No account associated with this token.", "error")
        return redirect(url_for("auth.login"))

    if user.is_verified:
        flash("Account already verified.", "info")
    else:
        user.is_verified = True
        db.session.commit()
        flash("Your email has been verified. You can now log in.", "success")

    return redirect(url_for("auth.login"))


# ──────────────────────────────────────────────────────────────────────────────
# 🔁 RESEND VERIFICATION EMAIL (requires login)
# ──────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/resend_verification")
@login_required
def resend_verification():
    if current_user.is_verified:
        flash("Your account is already verified.", "info")
    else:
        send_verification_email(current_user)
        flash("A new verification email has been sent.", "info")
    return redirect(url_for("auth.login"))


# ──────────────────────────────────────────────────────────────────────────────
# 🔑 RESET PASSWORD REQUEST: User submits email to get reset link
# ──────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()

        if user:
            send_password_reset_email(user)

        flash("If your email is registered, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html")


# ──────────────────────────────────────────────────────────────────────────────
# 🔄 RESET PASSWORD TOKEN HANDLER: Link from email opens reset form
# ──────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    try:
        email = get_token_serializer().loads(token, max_age=3600)
    except SignatureExpired:
        flash("This reset link has expired.", "error")
        return redirect(url_for('auth.reset_request'))
    except BadSignature:
        flash("Invalid or tampered reset link.", "error")
        return redirect(url_for('auth.reset_request'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("No user found for this token.", "error")
        return redirect(url_for('auth.reset_request'))

    if request.method == "POST":
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(request.url)

        user.password_hash = generate_password_hash(password)
        db.session.commit()
        flash("Your password has been updated. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_with_token.html")
