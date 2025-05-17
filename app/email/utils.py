import base64
import requests
from email.message import EmailMessage
from flask import url_for, current_app

from app.utils.token_utils import get_token_serializer
from app.utils.email_oauth import get_mail_access_token


def base64url_encode(message: bytes) -> str:
    """Encodes a message in base64 URL-safe format without padding."""
    return base64.urlsafe_b64encode(message).decode("utf-8").rstrip("=")


def send_verification_email(user):
    access_token = get_mail_access_token()
    if not access_token:
        print("❌ Could not get access token.")
        return False

    token = get_token_serializer().dumps(user.email)
    verify_link = url_for("auth.verify_token", token=token, _external=True)

    msg = EmailMessage()
    msg["Subject"] = "Verify Your Photo Share App Account"
    msg["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
    msg["To"] = user.email
    msg.set_content(f"""\
Hello {user.username},

Please verify your account by clicking the link below:
{verify_link}

This link is valid for 1 hour. If you didn't sign up, feel free to ignore this message.
""")

    raw_message = base64url_encode(msg.as_bytes())

    response = requests.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={
            "raw": raw_message
        }
    )

    if response.status_code == 200:
        print("✅ Verification email sent.")
        return True
    else:
        print("❌ Email failed:", response.text)
        return False


def send_password_reset_email(user):
    access_token = get_mail_access_token()
    if not access_token:
        print("❌ Could not get access token.")
        return False

    token = get_token_serializer().dumps(user.email)
    reset_link = url_for("auth.reset_token", token=token, _external=True)

    msg = EmailMessage()
    msg["Subject"] = "Reset Your Photo Share App Password"
    msg["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
    msg["To"] = user.email
    msg.set_content(f"""\
Hi {user.username},

You (or someone else) requested a password reset for your Photo Share App account.

Click the link below to reset your password:
{reset_link}

This link is valid for 1 hour. If you did not request this, you can ignore this message.
""")

    raw_message = base64url_encode(msg.as_bytes())

    response = requests.post(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={
            "raw": raw_message
        }
    )

    if response.status_code == 200:
        print("✅ Password reset email sent.")
        return True
    else:
        print("❌ Email failed:", response.text)
        return False
