import uuid
from pathlib import Path
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, abort
)
from flask_login import login_required, current_user
from PIL import Image
import pillow_heif # For HEIC support
from moviepy.video.io.VideoFileClip import VideoFileClip

from app.extensions import db # Make sure db is imported
from app.models import SharedAccess, Album, Photo # Import Album and Photo models
from app.routes.utils import (
    user_folder, sanitize_filename, allowed_file,
    load_json, save_json, DESCRIPTION_PATH, # ALBUM_PATH is no longer primary for photo-album links
    COMMENTS_PATH, TAGS_PATH, THUMB_FOLDER, VIDEO_EXTENSIONS
)

upload_bp = Blueprint('upload', __name__)

def generate_video_thumbnail(video_path: Path, thumb_path: Path) -> None:
    try:
        with VideoFileClip(str(video_path)) as clip:
            t = clip.duration / 2 if clip.duration > 1 else 0.1
            frame = clip.get_frame(t) # Corrected from clip.get_frame(t)
        img = Image.fromarray(frame)
        if img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        new_h = int(h * (320 / w))  # same as THUMB_SIZE_WIDTH
        img = img.resize((320, new_h), Image.Resampling.LANCZOS)
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(thumb_path), format="JPEG")
    except Exception as e:
        flash(f"Error generating video thumbnail for {video_path.name}: {e}", 'error')
        print(f"Thumbnail generation error for {video_path.name}: {e}") # Also print to console for debugging

@upload_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    shared_accesses = SharedAccess.query.filter_by(
        shared_user_id=current_user.id
    ).all()

    # For GET request: Populate album dropdown with current user's albums
    user_db_albums = Album.query.filter_by(user_id=current_user.id).order_by(Album.name).all()
    album_titles_for_dropdown = [album.name for album in user_db_albums]

    if request.method == "POST":
        owner_id_str = request.form.get("owner_id")
        try:
            owner_id = int(owner_id_str if owner_id_str else current_user.id)
        except ValueError:
            flash("Invalid owner ID specified.", "error")
            return redirect(url_for('upload.upload')) # Or handle error appropriately

        uploader_alias = current_user.username
        if owner_id != current_user.id:
            access = SharedAccess.query.filter_by(
                owner_id=owner_id,
                shared_user_id=current_user.id
            ).first()
            if not access or not access.can_upload:
                flash("You do not have permission to upload to this gallery.", "error")
                abort(403)
            uploader_alias = access.alias or current_user.username # Use alias if available

        files = request.files.getlist("photos")
        if not files or not any(f.filename for f in files):
            flash("No files selected for upload.", "warning")
            return redirect(request.url)

        selected_album_name = request.form.get("album", "").strip()
        new_album_name = request.form.get("new_album", "").strip()
        
        chosen_album_name_for_processing = new_album_name or selected_album_name
        target_album_id = None
        target_album_for_photo = None

        if chosen_album_name_for_processing:
            # Try to find or create the album associated with the owner_id
            # Check if new_album is specified, prioritize it
            if new_album_name:
                # Check if an album with this name already exists for the owner
                existing_album = Album.query.filter_by(name=new_album_name, user_id=owner_id).first()
                if existing_album:
                    target_album_for_photo = existing_album
                    flash(f"Using existing album: '{new_album_name}'.", "info")
                else:
                    try:
                        new_album_obj = Album(name=new_album_name, user_id=owner_id)
                        db.session.add(new_album_obj)
                        db.session.flush() # To get the ID if needed before commit, or for subsequent ops
                        target_album_for_photo = new_album_obj
                        flash(f"Created new album: '{new_album_name}'.", "success")
                    except Exception as e: # Catch potential db errors e.g. unique constraint
                        db.session.rollback()
                        flash(f"Error creating new album '{new_album_name}': {e}", "error")
                        # Decide if you want to proceed without an album or stop
                        # For now, we'll proceed without an album if creation fails
                        target_album_for_photo = None 
            elif selected_album_name: # An existing album was chosen from dropdown
                target_album_for_photo = Album.query.filter_by(name=selected_album_name, user_id=owner_id).first()
                if not target_album_for_photo:
                    flash(f"Selected album '{selected_album_name}' not found for the target gallery. Uploading without album.", "warning")
            
            if target_album_for_photo:
                target_album_id = target_album_for_photo.id


        # --- JSON data for descriptions, comments, tags (still using JSON for these as per original code) ---
        # Consider migrating these to the database as well for consistency in the future.
        descs = load_json(DESCRIPTION_PATH)
        comments = load_json(COMMENTS_PATH)
        tags = load_json(TAGS_PATH)
        # --- End JSON data loading ---

        UPLOAD_FOLDER = user_folder(owner_id)
        uploaded_count = 0

        for file in files:
            if file and file.filename and allowed_file(file.filename):
                original_sanitized_filename = sanitize_filename(file.filename)
                file_ext = original_sanitized_filename.rsplit('.', 1)[1].lower()
                
                # Generate a unique filename for storage to prevent overwrites and invalid chars
                unique_storage_filename = f"{uuid.uuid4().hex}.{file_ext}"
                save_path = UPLOAD_FOLDER / unique_storage_filename
                
                photo_media_type = 'image' # Default

                try:
                    if file_ext == 'heic':
                        pillow_heif.register_heif_opener() # Ensure HEIF opener is registered
                        heif_file = pillow_heif.read_heif(file.stream)
                        img = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw")
                        
                        # Update filename and save_path for the converted JPG
                        unique_storage_filename = f"{save_path.stem}.jpg" # use same stem, new extension
                        save_path = UPLOAD_FOLDER / unique_storage_filename
                        img.save(str(save_path), format='JPEG')
                        flash(f"HEIC file '{original_sanitized_filename}' converted to JPEG and saved as '{unique_storage_filename}'.", "info")
                    else:
                        file.stream.seek(0) # Reset stream position before saving
                        file.save(str(save_path))

                    if file_ext in VIDEO_EXTENSIONS:
                        photo_media_type = 'video'
                        thumb_file_path = THUMB_FOLDER / f"{save_path.stem}.jpg"
                        generate_video_thumbnail(save_path, thumb_file_path)

                    # Create Photo DB record
                    new_photo = Photo(
                        filename=unique_storage_filename,
                        original_filename=original_sanitized_filename,
                        user_id=owner_id,
                        album_id=target_album_id # Assign album_id
                        # media_type=photo_media_type # If you add this field to Photo model
                    )
                    db.session.add(new_photo)
                    
                    # --- Update JSON metadata for this photo (filename is unique_storage_filename) ---
                    # This part might be phased out if descriptions, comments, tags move to Photo model
                    if target_album_for_photo: # If there's an album, old JSON 'albums' is not updated
                        pass # albums[unique_storage_filename] = target_album_for_photo.name # No longer saving album name to JSON
                    
                    descs.setdefault(unique_storage_filename, "")
                    tags.setdefault(unique_storage_filename, [])
                    photo_comments = comments.setdefault(unique_storage_filename, [])
                    photo_comments.insert(0, f"Uploaded by {uploader_alias}") # Prepends comment
                    # --- End JSON metadata update ---

                    uploaded_count += 1

                except Exception as e:
                    db.session.rollback() # Rollback for this photo's transaction part
                    flash(f"Error processing file {original_sanitized_filename}: {e}", "error")
                    print(f"Error processing file {original_sanitized_filename}: {e}") # Log error
                    # Continue to next file if one fails
                    continue
        
        if uploaded_count > 0:
            try:
                db.session.commit() # Commit all new Photo objects and potentially new Album
                
                # --- Save JSON files (excluding album if it's fully DB based now) ---
                save_json(DESCRIPTION_PATH, descs)
                # save_json(ALBUM_PATH, albums) # ALBUM_PATH JSON no longer stores filename-to-album_name map
                save_json(COMMENTS_PATH, comments)
                save_json(TAGS_PATH, tags)
                # --- End saving JSON files ---
                
                flash(f"{uploaded_count} file(s) uploaded successfully.", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Database error after uploading files: {e}", "error")
                print(f"Database commit error: {e}")
        elif not files or not any(f.filename for f in files) and (selected_album_name or new_album_name) and not target_album_id and new_album_name:
            # This case handles if only a new album was to be created but no files uploaded or files failed.
            # If an album object (new_album_obj) was added to session and creation failed earlier, it was rolled back.
            # If it was successful and added, but no photos, we might want to commit it or not.
            # Current logic: if new_album_obj was created and added to session, and flush was successful,
            # it will be committed here IF uploaded_count is >0.
            # If uploaded_count is 0, but an album was added to session, it won't be committed.
            # This behavior might need adjustment depending on desired outcome for "create album without photos".
            # For now, if a new album was added to session and flush() succeeded, but commit happens only if files uploaded.
            # We can explicitly commit a new album if it was created:
            if target_album_for_photo and target_album_for_photo.id is None and new_album_name: # Check if it's a new, uncommitted album.
                 try:
                     db.session.commit()
                     flash(f"Album '{new_album_name}' created successfully, but no files were uploaded with it.", "info")
                 except Exception as e:
                     db.session.rollback()
                     flash(f"Error saving newly created album '{new_album_name}' without files: {e}", "error")
        
        return redirect(url_for('gallery.index')) # Or 'upload.upload' to stay on page

    # For GET request
    return render_template(
        'upload.html',
        shared_accesses=shared_accesses,
        album_titles=album_titles_for_dropdown # Pass the DB-driven album names
    )