from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def get_token_serializer():
    secret_key = current_app.config.get("SECRET_KEY", "dev")
    return URLSafeTimedSerializer(secret_key)
