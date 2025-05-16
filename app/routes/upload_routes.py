import uuid
from pathlib import Path
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, abort
)
from flask_login import login_required, current_user
from PIL import Image
import pillow_heif
from moviepy.video.io.VideoFileClip import VideoFileClip
from app.models import SharedAccess
from app.routes.utils import (
    user_folder, sanitize_filename, allowed_file,
    load_json, save_json, DESCRIPTION_PATH, ALBUM_PATH,
    COMMENTS_PATH, TAGS_PATH, THUMB_FOLDER, VIDEO_EXTENSIONS
)

upload_bp = Blueprint('upload', __name__)

def generate_video_thumbnail(video_path: Path, thumb_path: Path) -> None:
    try:
        with VideoFileClip(str(video_path)) as clip:
            t = clip.duration / 2 if clip.duration > 1 else 0.1
            frame = clip.get_frame(t)
        img = Image.fromarray(frame)
        if img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        new_h = int(h * (320 / w))  # same as THUMB_SIZE_WIDTH
        img = img.resize((320, new_h), Image.Resampling.LANCZOS)
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(thumb_path), format="JPEG")
    except Exception as e:
        flash(f"Error generating video thumbnail: {e}", 'error')

@upload_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    shared_accesses = SharedAccess.query.filter_by(
        shared_user_id=current_user.id
    ).all()
    albums_map = load_json(ALBUM_PATH)
    album_titles = sorted(
        {v for k, v in albums_map.items() if k != "favorites"},
        key=str.lower
    )

    if request.method == "POST":
        owner_id = int(request.form.get("owner_id", current_user.id))
        if owner_id != current_user.id:
            access = SharedAccess.query.filter_by(
                owner_id=owner_id,
                shared_user_id=current_user.id
            ).first()
            if not access or not access.can_upload:
                abort(403)
            uploader_alias = access.alias
        else:
            uploader_alias = current_user.username

        files = request.files.getlist("photos")
        album = request.form.get("album", "").strip()
        new_album = request.form.get("new_album", "").strip()
        chosen_album = new_album or album

        descs    = load_json(DESCRIPTION_PATH)
        albums   = load_json(ALBUM_PATH)
        comments = load_json(COMMENTS_PATH)
        tags     = load_json(TAGS_PATH)

        UPLOAD_FOLDER = user_folder(owner_id)

        for file in files:
            if file and allowed_file(file.filename):
                orig = sanitize_filename(file.filename)
                ext  = orig.rsplit('.', 1)[1].lower()
                filename = f"{uuid.uuid4().hex}.{ext}"
                save_path = UPLOAD_FOLDER / filename

                if ext == 'heic':
                    try:
                        hf = pillow_heif.read_heif(file.stream)
                        img = Image.frombytes(hf.mode, hf.size, hf.data, 'raw')
                        filename = f"{uuid.uuid4().hex}.jpg"
                        save_path = UPLOAD_FOLDER / filename
                        img.save(str(save_path), format='JPEG')
                        flash('HEIC converted and uploaded.', 'success')
                    except Exception as e:
                        flash(f'HEIC conversion failed: {e}', 'error')
                        continue
                else:
                    file.save(str(save_path))

                if ext in VIDEO_EXTENSIONS:
                    thumb_file = THUMB_FOLDER / f"{save_path.stem}.jpg"
                    generate_video_thumbnail(save_path, thumb_file)

                if chosen_album:
                    albums[filename] = chosen_album
                descs.setdefault(filename, "")
                comments.setdefault(filename, [])
                tags.setdefault(filename, [])

                comments[filename].insert(0, f"Uploaded by {uploader_alias}")

        save_json(DESCRIPTION_PATH, descs)
        save_json(ALBUM_PATH, albums)
        save_json(COMMENTS_PATH, comments)
        save_json(TAGS_PATH, tags)

        flash('Upload successful.', 'success')
        return redirect(url_for('gallery.index'))

    return render_template(
        'upload.html',
        shared_accesses=shared_accesses,
        album_titles=album_titles
    )
