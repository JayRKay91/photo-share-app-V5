import json
from urllib.parse import unquote
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify, abort
)
from flask_login import login_required, current_user
from pathlib import Path
from app.routes.utils import (
    load_json, save_json, allowed_file, user_folder,
    sanitize_filename, ALBUM_PATH, DESCRIPTION_PATH,
    COMMENTS_PATH, TAGS_PATH, THUMB_FOLDER,
    IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
)

album_bp = Blueprint('album', __name__)

@album_bp.route("/albums")
@login_required
def albums():
    raw_data = load_json(ALBUM_PATH)
    albums_map = {k: v for k, v in raw_data.items() if k != "favorites"}

    UPLOAD_FOLDER = user_folder(current_user.id)
    media_files = sorted(
        [f for f in UPLOAD_FOLDER.iterdir() if f.is_file() and allowed_file(f.name)],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    album_titles = sorted({v for v in albums_map.values()}, key=str.lower)
    grouped = {title: [] for title in album_titles}

    for f in media_files:
        fn = f.name
        title = albums_map.get(fn, "")
        if title in grouped:
            grouped[title].append(f)

    albums_data = []
    for title in album_titles:
        files = grouped.get(title, [])
        photos = sum(1 for f in files if f.suffix.lstrip('.').lower() in IMAGE_EXTENSIONS)
        videos = sum(1 for f in files if f.suffix.lstrip('.').lower() in VIDEO_EXTENSIONS)

        thumbnails = []
        for f in files[:5]:
            ext = f.suffix.lstrip('.').lower()
            if ext in VIDEO_EXTENSIONS:
                thumbnails.append(url_for('gallery.thumbnail', filename=f"{f.stem}.jpg"))
            else:
                thumbnails.append(url_for('gallery.uploaded_file', filename=f.name))

        albums_data.append({
            "title": title,
            "photos": photos,
            "videos": videos,
            "thumbnails": thumbnails
        })

    favorites_map = raw_data.get("favorites", {})
    user_favorites = favorites_map.get(str(current_user.id), [])

    return render_template("albums.html", albums_data=albums_data, favorites=user_favorites)


@album_bp.route("/album/<album_title>")
@login_required
def view_album(album_title):
    descs    = load_json(DESCRIPTION_PATH)
    albums   = load_json(ALBUM_PATH)
    comments = load_json(COMMENTS_PATH)
    tags     = load_json(TAGS_PATH)

    decoded_title = unquote(album_title).strip().lower()
    actual_album_title = next(
        (v for v in albums.values() if isinstance(v, str) and v.strip().lower() == decoded_title),
        None
    )

    if not actual_album_title:
        flash(f"No album found named '{unquote(album_title)}'", "error")
        return redirect(url_for("album.albums"))

    UPLOAD_FOLDER = user_folder(current_user.id)
    media_files = sorted(
        [
            f for f in UPLOAD_FOLDER.iterdir()
            if f.is_file()
            and allowed_file(f.name)
            and albums.get(f.name) == actual_album_title
        ],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    media = []
    for path in media_files:
        fn  = path.name
        ext = path.suffix.lstrip('.').lower()
        media_type = "video" if ext in VIDEO_EXTENSIONS else "image"
        thumb = (
            url_for('gallery.thumbnail', filename=f"{path.stem}.jpg")
            if media_type == "video"
            else url_for('gallery.uploaded_file', filename=fn)
        )
        media.append({
            "filename": fn,
            "description": descs.get(fn, ""),
            "tags": tags.get(fn, []),
            "comments": comments.get(fn, []),
            "type": media_type,
            "thumb": thumb
        })

    return render_template(
        "album_view.html",
        album_title=actual_album_title,
        media_items=media
    )

@album_bp.route("/create_album", methods=["POST"])
@login_required
def create_album():
    name = request.form.get("title", "").strip()
    if not name:
        flash("Album name cannot be empty.", "error")
    elif len(name) > 50:
        flash("Album name must be 50 characters or fewer.", "error")
    else:
        data = load_json(ALBUM_PATH)
        favorites = data.get("favorites")
        albums_map = {k: v for k, v in data.items() if k != "favorites"}
        existing = set(albums_map.values())

        if name in existing:
            flash(f"Album '{name}' already exists.", "info")
        else:
            albums_map[name] = name
            new_data = dict(albums_map)
            if favorites is not None:
                new_data["favorites"] = favorites
            save_json(ALBUM_PATH, new_data)
            flash(f"Album '{name}' created.", "success")

    return redirect(url_for("album.albums"))

@album_bp.route("/toggle_favorite_album", methods=["POST"])
@login_required
def toggle_favorite_album():
    album = request.form.get("album", "").strip()
    if not album:
        return jsonify({"status": "error", "message": "No album specified"}), 400

    data = load_json(ALBUM_PATH)
    favorites = data.get("favorites", {})
    user_id_str = str(current_user.id)
    user_favs = favorites.get(user_id_str, [])

    if album in user_favs:
        user_favs.remove(album)
        action = "unfavorited"
    else:
        user_favs.append(album)
        action = "favorited"

    favorites[user_id_str] = user_favs
    data["favorites"] = favorites
    save_json(ALBUM_PATH, data)

    return jsonify({"status": "success", "action": action})


@album_bp.route("/delete_album", methods=["POST"])
@login_required
def delete_album():
    data = request.get_json()
    album_title = data.get("album_title", "").strip()

    if not album_title:
        return jsonify({"error": "Missing album title"}), 400

    try:
        with open(ALBUM_PATH, "r") as f:
            albums = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        albums = {}

    albums_to_keep = {
        k: v for k, v in albums.items()
        if v != album_title and k != "favorites"
    }

    favorites = albums.get("favorites", {})
    uid = str(current_user.id)
    if uid in favorites:
        favorites[uid] = [t for t in favorites[uid] if t != album_title]

    albums_to_keep["favorites"] = favorites
    with open(ALBUM_PATH, "w") as f:
        json.dump(albums_to_keep, f, indent=2)

    return jsonify({"success": True}), 200


@album_bp.route("/rename_album/<album_title>", methods=["POST"])
@login_required
def rename_album(album_title):
    old_title = unquote(album_title).strip()
    payload = request.get_json(silent=True) or {}
    new_title = payload.get("new_title", "").strip()
    if not new_title:
        return jsonify({"status": "error", "message": "No new title provided"}), 400

    data = load_json(ALBUM_PATH)
    favorites = data.get("favorites", {})

    updated_map = {}
    for key, value in data.items():
        if key == "favorites":
            continue
        if key == old_title and value == old_title:
            updated_map[new_title] = new_title
        elif value == old_title:
            updated_map[key] = new_title
        else:
            updated_map[key] = value

    for user_id, fav_list in favorites.items():
        favorites[user_id] = [new_title if t == old_title else t for t in fav_list]

    result = dict(updated_map)
    result["favorites"] = favorites
    save_json(ALBUM_PATH, result)

    return jsonify({"status": "success"}), 200
