from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from urllib.parse import unquote
from pathlib import Path
from sqlalchemy import func

from app import db
from app.models import Album, Photo
from app.routes.utils import (
    load_json,
    DESCRIPTION_PATH,
    COMMENTS_PATH,
    TAGS_PATH,
    allowed_file,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS
)

album_bp = Blueprint('album', __name__)

@album_bp.route('/albums')
@login_required
def albums():
    user_albums = Album.query.filter_by(user_id=current_user.id).order_by(func.lower(Album.title)).all()
    albums_data = []
    for album in user_albums:
        media_records = [
            p for p in Photo.query.filter_by(user_id=current_user.id, album_id=album.id).all()
            if allowed_file(p.filename)
        ]
        photos_count = sum(
            1 for p in media_records
            if p.filename.rsplit('.', 1)[1].lower() in IMAGE_EXTENSIONS
        )
        videos_count = sum(
            1 for p in media_records
            if p.filename.rsplit('.', 1)[1].lower() in VIDEO_EXTENSIONS
        )
        recent_media = sorted(media_records, key=lambda p: p.id, reverse=True)[:5]
        thumbnails = []
        for p in recent_media:
            ext = p.filename.rsplit('.', 1)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                thumb = url_for('gallery.thumbnail', filename=p.filename.rsplit('.', 1)[0] + '.jpg')
            else:
                thumb = url_for('gallery.uploaded_file', filename=p.filename)
            thumbnails.append(thumb)
        albums_data.append({
            'title': album.title,
            'photos': photos_count,
            'videos': videos_count,
            'thumbnails': thumbnails
        })
    user_favorites = [album.title for album in user_albums if getattr(album, 'favorite', False)]
    return render_template('albums.html', albums_data=albums_data, favorites=user_favorites)

@album_bp.route('/album/<album_title>')
@login_required
def view_album(album_title):
    descs = load_json(DESCRIPTION_PATH)
    comments = load_json(COMMENTS_PATH)
    tags = load_json(TAGS_PATH)
    decoded_title = unquote(album_title).strip()
    album = Album.query.filter(
        Album.user_id == current_user.id,
        func.lower(Album.title) == decoded_title.lower()
    ).first()
    if not album:
        flash('No album found named ' + decoded_title, 'error')
        return redirect(url_for('album.albums'))
    media_records = [
        p for p in Photo.query.filter_by(user_id=current_user.id, album_id=album.id).all()
        if allowed_file(p.filename)
    ]
    media_sorted = sorted(media_records, key=lambda p: p.id, reverse=True)
    media_items = []
    for p in media_sorted:
        ext = p.filename.rsplit('.', 1)[1].lower()
        media_type = 'video' if ext in VIDEO_EXTENSIONS else 'image'
        if media_type == 'video':
            thumb = url_for('gallery.thumbnail', filename=p.filename.rsplit('.', 1)[0] + '.jpg')
        else:
            thumb = url_for('gallery.uploaded_file', filename=p.filename)
        media_items.append({
            'filename': p.filename,
            'description': descs.get(p.filename, ''),
            'tags': tags.get(p.filename, []),
            'comments': comments.get(p.filename, []),
            'type': media_type,
            'thumb': thumb
        })
    return render_template('album_view.html', album_title=album.title, media_items=media_items)

@album_bp.route('/create_album', methods=['POST'])
@login_required
def create_album():
    name = request.form.get('title', '').strip()
    if not name:
        flash('Album name cannot be empty.', 'error')
    elif len(name) > 50:
        flash('Album name must be 50 characters or fewer.', 'error')
    elif Album.query.filter_by(user_id=current_user.id, title=name).first():
        flash('Album ' + name + ' already exists.', 'info')
    else:
        new_album = Album(title=name, user_id=current_user.id, favorite=False)
        db.session.add(new_album)
        db.session.commit()
        flash('Album ' + name + ' created.', 'success')
    return redirect(url_for('album.albums'))

@album_bp.route('/toggle_favorite_album', methods=['POST'])
@login_required
def toggle_favorite_album():
    album_name = request.form.get('album', '').strip()
    if not album_name:
        return jsonify({'status': 'error', 'message': 'No album specified'}), 400
    album = Album.query.filter_by(user_id=current_user.id, title=album_name).first()
    if not album:
        return jsonify({'status': 'error', 'message': 'Album not found'}), 404
    album.favorite = not getattr(album, 'favorite', False)
    db.session.commit()
    action = 'favorited' if album.favorite else 'unfavorited'
    return jsonify({'status': 'success', 'action': action})

@album_bp.route('/delete_album', methods=['POST'])
@login_required
def delete_album():
    data = request.get_json() or {}
    album_title = data.get('album_title', '').strip()
    if not album_title:
        return jsonify({'error': 'Missing album title'}), 400
    album = Album.query.filter(
        Album.user_id == current_user.id,
        func.lower(Album.title) == album_title.lower()
    ).first()
    if not album:
        return jsonify({'error': 'Album not found'}), 404
    db.session.delete(album)
    db.session.commit()
    return jsonify({'success': True}), 200

@album_bp.route('/rename_album/<album_title>', methods=['POST'])
@login_required
def rename_album(album_title):
    old_title = unquote(album_title).strip()
    payload = request.get_json() or {}
    new_title = payload.get('new_title', '').strip()
    if not new_title:
        return jsonify({'status': 'error', 'message': 'No new title provided'}), 400
    album = Album.query.filter(
        Album.user_id == current_user.id,
        func.lower(Album.title) == old_title.lower()
    ).first()
    if not album:
        return jsonify({'status': 'error', 'message': 'Album not found'}), 404
    if Album.query.filter(
        Album.user_id == current_user.id,
        func.lower(Album.title) == new_title.lower()
    ).first():
        return jsonify({'status': 'error', 'message': 'Album with that name already exists'}), 400
    album.title = new_title
    db.session.commit()
    return jsonify({'status': 'success'}), 200
