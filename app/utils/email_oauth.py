# email_oauth.py
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def get_mail_access_token():
    creds = Credentials(
        token=None,
        refresh_token=os.getenv('OAUTH2_REFRESH_TOKEN'),
        client_id=os.getenv('OAUTH2_CLIENT_ID'),
        client_secret=os.getenv('OAUTH2_CLIENT_SECRET'),
        token_uri='https://oauth2.googleapis.com/token',
    )
    creds.refresh(Request())
    return creds.token
