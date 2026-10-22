"""Gmail API (read-only) source for alert emails. Needs the `gmail` extra.

One-time consent: put an OAuth client at config/gmail_client.json; the token is
stored at config/gmail_token.json (both gitignored).
"""
import base64
from pathlib import Path
from typing import Iterator

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def _service(config_dir: Path):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    token = config_dir / "gmail_token.json"
    creds = Credentials.from_authorized_user_file(token, SCOPES) if token.exists() else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config_dir / "gmail_client.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        token.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def _html_body(payload: dict) -> str:
    if payload.get("mimeType") == "text/html" and payload["body"].get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", "replace")
    for part in payload.get("parts", []):
        html = _html_body(part)
        if html:
            return html
    return ""


def fetch_alerts(query: str, max_messages: int, config_dir: Path = Path("config")) -> Iterator[tuple[str, str]]:
    """Yield (message_id, html_body) for messages matching query."""
    svc = _service(config_dir).users().messages()
    resp = svc.list(userId="me", q=query, maxResults=max_messages).execute()
    for m in resp.get("messages", []):
        full = svc.get(userId="me", id=m["id"], format="full").execute()
        yield m["id"], _html_body(full["payload"])
