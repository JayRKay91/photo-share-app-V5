from flask import (
    Blueprint, render_template, request, url_for,
    send_from_directory, flash, redirect
)
from flask_login import login_required, current_user
from pathlib import Path
from app.extensions import db
from app.models import SharedAccess
from werkzeug.utils import secure_filename
from app.routes.utils import (
    load_json, save_json, sanitize_filename,
    user_folder, DESCRIPTION_PATH, ALBUM_PATH, COMMENTS_PATH, TAGS_PATH,
    THUMB_FOLDER, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
)

gallery_bp = Blueprint('gallery', __name__)

@gallery_bp.route("/")
@login_required
def index():
    descs    = load_json(DESCRIPTION_PATH)
    albums   = load_json(ALBUM_PATH)
    comments = load_json(COMMENTS_PATH)
    tags     = load_json(TAGS_PATH)

    tag_filter   = request.args.get("tag", "").strip().lower()
    search_query = request.args.get("search", "").strip().lower()

    UPLOAD_FOLDER = user_folder(current_user.id)
    media_files = sorted(
        [f for f in UPLOAD_FOLDER.iterdir() if f.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    images = []
    for path in media_files:
        fn  = path.name
        ext = path.suffix.lstrip('.').lower()
        file_tags = tags.get(fn, [])
        lt = [t.lower() for t in file_tags]

        if tag_filter and tag_filter not in lt:
            continue
        if search_query and not (
            search_query in fn.lower()
            or search_query in descs.get(fn, "").lower()
            or search_query in albums.get(fn, "").lower()
            or any(search_query in t.lower() for t in file_tags)
        ):
            continue

        media_type = "video" if ext in VIDEO_EXTENSIONS else "image"
        thumb = (
            url_for('gallery.thumbnail', filename=f"{path.stem}.jpg")
            if media_type == "video"
            else url_for('gallery.uploaded_file', filename=fn)
        )

        images.append({
            "filename": fn,
            "description": descs.get(fn, ""),
            "album": albums.get(fn, ""),
            "comments": comments.get(fn, []),
            "tags": file_tags,
            "type": media_type,
            "thumb": thumb,
        })

    all_tags = sorted({t for lst in tags.values() for t in lst}, key=str.lower)

    shared_accesses = SharedAccess.query.filter_by(
        shared_user_id=current_user.id
    ).all()

    favorites_map = load_json(ALBUM_PATH).get("favorites", {})
    user_favorites = favorites_map.get(str(current_user.id), [])

    return render_template(
        "gallery.html",
        images=images,
        descriptions=descs,
        albums=albums,
        tags=tags,
        all_tags=all_tags,
        current_tag=tag_filter,
        search_query=search_query,
        shared_accesses=shared_accesses,
        favorites=user_favorites
    )

@gallery_bp.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):
    fn = sanitize_filename(filename)
    user_dir = user_folder(current_user.id)
    return send_from_directory(str(user_dir), fn)

@gallery_bp.route("/thumbnails/<filename>")
@login_required
def thumbnail(filename):
    fn = sanitize_filename(filename)
    return send_from_directory(str(THUMB_FOLDER), fn)

@gallery_bp.route("/download/<filename>")
@login_required
def download_image(filename):
    fn = sanitize_filename(filename)
    UPLOAD_FOLDER = user_folder(current_user.id)
    return send_from_directory(str(UPLOAD_FOLDER), fn, as_attachment=True)

@gallery_bp.route("/update_description/<filename>", methods=["POST"])
@login_required
def update_description(filename):
    fn = sanitize_filename(filename)
    descs = load_json(DESCRIPTION_PATH)
    descs[fn] = request.form.get("description", "").strip()
    save_json(DESCRIPTION_PATH, descs)
    flash("Description updated.", 'success')
    return redirect(url_for('gallery.index'))

@gallery_bp.route("/delete/<filename>", methods=["POST"])
@login_required
def delete_image(filename):
    fn = sanitize_filename(filename)
    UPLOAD_FOLDER = user_folder(current_user.id)
    file_path = UPLOAD_FOLDER / fn

    # Remove original media file
    if file_path.exists():
        file_path.unlink()

    # Remove video thumbnail if it exists
    thumb_path = THUMB_FOLDER / f"{Path(fn).stem}.jpg"
    if thumb_path.exists():
        thumb_path.unlink()

    # Remove metadata
    for path in [DESCRIPTION_PATH, TAGS_PATH, COMMENTS_PATH, ALBUM_PATH]:
        data = load_json(path)
        if fn in data:
            del data[fn]
            save_json(path, data)

    flash(f"{fn} deleted.", "success")
    return redirect(url_for("gallery.index"))
