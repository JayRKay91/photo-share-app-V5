import json
from pathlib import Path
from flask import current_app, abort
from werkzeug.utils import secure_filename

# ─── Paths ─────────────────────────────────────────────
BASE_DIR         = Path(__file__).resolve().parent.parent.parent
UPLOAD_BASE      = BASE_DIR / "uploads"
DATA_DIR         = BASE_DIR
DESCRIPTION_PATH = DATA_DIR / "descriptions.json"
ALBUM_PATH       = DATA_DIR / "albums.json"
COMMENTS_PATH    = DATA_DIR / "comments.json"
TAGS_PATH        = DATA_DIR / "tags.json"
THUMB_FOLDER     = BASE_DIR / "app" / "static" / "thumbnails"

# ─── Allowed File Types ────────────────────────────────
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "heic"}
VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS

# ─── Ensure directories exist ──────────────────────────
UPLOAD_BASE.mkdir(parents=True, exist_ok=True)
THUMB_FOLDER.mkdir(parents=True, exist_ok=True)

# ─── Helper Functions ──────────────────────────────────
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def sanitize_filename(filename: str) -> str:
    clean = secure_filename(filename)
    if clean != filename:
        abort(400, "Invalid filename.")
    return filename

def load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            current_app.logger.error(f"Invalid JSON in {path}")
    return {}

def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2))

def user_folder(user_id: int) -> Path:
    path = UPLOAD_BASE / str(user_id)
    path.mkdir(parents=True, exist_ok=True)
    return path
