import os
from app.utils.email_oauth import get_mail_access_token

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration."""

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(basedir, 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads
    UPLOAD_FOLDER = os.path.join(basedir, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024 * 1024  # 10 GB

    # Email (Gmail SMTP via OAuth2)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ("true", "1", "yes")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

    # OAuth2 helper for fetching the SMTP bearer token