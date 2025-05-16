from flask import (
    Blueprint, request, redirect, url_for,
    flash, abort
)
from flask_login import login_required, current_user
from app.models import SharedAccess
from app.routes.utils import (
    sanitize_filename, load_json, save_json, COMMENTS_PATH
)

comment_bp = Blueprint('comment', __name__)

@comment_bp.route("/add_comment/<filename>", methods=["POST"])
@login_required
def add_comment(filename):
    fn = sanitize_filename(filename)
    comment_text = request.form.get("comment", "").strip()
    if not comment_text:
        flash("Empty comment not added.", 'warning')
        return redirect(url_for('gallery.index'))

    owner_id = int(request.form.get("owner_id", current_user.id))
    if owner_id != current_user.id:
        access = SharedAccess.query.filter_by(
            owner_id=owner_id,
            shared_user_id=current_user.id
        ).first()
        if not access or not access.can_comment:
            abort(403)
        commenter_alias = access.alias
    else:
        commenter_alias = current_user.username

    comments = load_json(COMMENTS_PATH)
    comments.setdefault(fn, [])
    comments[fn].append(f"{commenter_alias} — {comment_text}")
    save_json(COMMENTS_PATH, comments)

    flash("Comment added.", 'success')
    return redirect(url_for('gallery.index'))
