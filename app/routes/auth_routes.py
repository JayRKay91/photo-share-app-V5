from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

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
            is_verified=True  # change to False if using real verification
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Account created! Please verify your email before logging in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You’ve been logged out.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if request.method == 'POST':
        email = request.form.get('email')
        # Lookup user and send reset email logic
        flash('If your email is registered, a reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html')

@auth_bp.route('/verify')
def verify_email():
    return render_template('auth/verify_email.html')

@auth_bp.route('/resend_verification')
def resend_verification():
    # Logic to resend email here
    flash('A new verification email has been sent.', 'info')
    return redirect(url_for('auth.login'))

from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app

# --- Token Serializer ---
def get_token_serializer():
    secret_key = current_app.config.get("SECRET_KEY", "dev")  # update for production
    return URLSafeTimedSerializer(secret_key)

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    serializer = get_token_serializer()

    try:
        email = serializer.loads(token, max_age=3600)  # valid for 1 hour
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

    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(request.url)

        user.password_hash = generate_password_hash(password)
        db.session.commit()
        flash("Your password has been updated. Please log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_with_token.html')
