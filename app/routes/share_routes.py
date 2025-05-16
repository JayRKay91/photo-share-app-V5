from flask import (
    Blueprint, request, redirect, url_for,
    flash
)
from flask_login import login_required, current_user
from app.models import db, User, SharedAccess

share_bp = Blueprint('share', __name__)

@share_bp.route("/share", methods=["POST"])
@login_required
def share():
    primary_id = current_user.id
    shared_username = request.form.get("username")
    alias = request.form.get("alias", "").strip() or None

    user = User.query.filter_by(username=shared_username).first()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('gallery.index'))

    existing = SharedAccess.query.filter_by(
        owner_id=primary_id,
        shared_user_id=user.id
    ).first()
    if existing:
        flash('Access already granted', 'info')
        return redirect(url_for('gallery.index'))

    access = SharedAccess(
        owner_id=primary_id,
        shared_user_id=user.id,
        alias=alias or user.username,
        can_upload=True,
        can_comment=True
    )
    db.session.add(access)
    db.session.commit()

    flash(f"Granted gallery access to {user.username}", 'success')
    return redirect(url_for('gallery.index'))
