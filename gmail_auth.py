import os
import pickle
from pathlib import Path
import streamlit as st
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_FILE = Path("token.pkl")
CLIENT_SECRET = Path(os.getenv("GMAIL_CLIENT_SECRET", "client_secret.json"))

def get_gmail_service():
    """Return an authenticated Gmail service (pickle token cache)."""
    creds = None
    if TOKEN_FILE.exists():
        creds = pickle.loads(TOKEN_FILE.read_bytes())
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET.exists():
                st.error(
                    "client_secret.json not found. Upload it or set GMAIL_CLIENT_SECRET path environment variable."
                )
                st.stop()
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_bytes(pickle.dumps(creds))
    return build("gmail", "v1", credentials=creds, cache_discovery=False)