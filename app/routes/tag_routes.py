from flask import (
    Blueprint, request, redirect, url_for,
    flash
)
from flask_login import login_required
from app.routes.utils import (
    sanitize_filename, load_json, save_json,
    TAGS_PATH
)

tag_bp = Blueprint('tag', __name__)

@tag_bp.route("/add_tag/<filename>", methods=["POST"])
@login_required
def add_tag(filename):
    fn = sanitize_filename(filename)
    tags = load_json(TAGS_PATH)
    new = request.form.get("tag", "").strip()
    if new:
        tags.setdefault(fn, [])
        if new not in tags[fn]:
            tags[fn].append(new)
            save_json(TAGS_PATH, tags)
            flash(f"Tag '{new}' added.", 'success')
        else:
            flash(f"Tag '{new}' exists.", 'info')
    else:
        flash("Empty tag not added.", 'warning')
    return redirect(url_for('gallery.index'))

@tag_bp.route("/remove_tag/<filename>/<tag>", methods=["POST"])
@login_required
def remove_tag(filename, tag):
    fn = sanitize_filename(filename)
    tags = load_json(TAGS_PATH)
    tags.setdefault(fn, [])
    tags[fn] = [t for t in tags[fn] if t.lower() != tag.lower()]
    save_json(TAGS_PATH, tags)
    flash(f"Tag '{tag}' removed.", 'success')
    return redirect(url_for('gallery.index'))

@tag_bp.route("/rename_tag_single", methods=["POST"])
@login_required
def rename_tag_single():
    fn = sanitize_filename(request.form.get("filename", ""))
    old = request.form.get("old_tag", "").strip().lower()
    new = request.form.get("new_tag", "").strip()
    if not old or not new:
        flash("Missing rename data.", 'warning')
        return redirect(url_for('gallery.index'))

    tags = load_json(TAGS_PATH)
    tags.setdefault(fn, [])
    tags[fn] = [new if t.lower() == old else t for t in tags[fn]]
    save_json(TAGS_PATH, tags)
    flash(f"Renamed '{old}'→'{new}' on {fn}.", 'success')
    return redirect(url_for('gallery.index'))

@tag_bp.route("/rename_tag_global", methods=["POST"])
@login_required
def rename_tag_global():
    old = request.form.get("old_tag", "").strip().lower()
    new = request.form.get("new_tag", "").strip()
    if not old or not new:
        flash("Missing rename data.", 'warning')
        return redirect(url_for('gallery.index'))

    tags = load_json(TAGS_PATH)
    updated = False
    for fn, lst in tags.items():
        new_lst = [new if t.lower() == old else t for t in lst]
        if new_lst != lst:
            tags[fn] = new_lst
            updated = True

    if updated:
        save_json(TAGS_PATH, tags)
        flash(f"Renamed '{old}'→'{new}' globally.", 'success')
    else:
        flash(f"No matches for '{old}'.", 'info')
    return redirect(url_for('gallery.index'))

@tag_bp.route("/tag/<tagname>")
@login_required
def filter_by_tag(tagname):
    return redirect(url_for('gallery.index', tag=tagname))
