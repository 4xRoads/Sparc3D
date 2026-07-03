"""Thin wrapper around the Gmail API for one mailbox.

Handles OAuth (per-account token cached on disk), sending MIME mail, and the
receiver-side engagement actions that actually build sender reputation:
rescuing messages from spam, marking read, starring, and replying.
"""

from __future__ import annotations

import base64
import os
from email.mime.text import MIMEText
from email.utils import formataddr, make_msgid
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Full mail scope: we send, read, and modify labels (spam rescue, star, read).
SCOPES = ["https://mail.google.com/"]


class GmailClient:
    def __init__(self, email: str, credentials_file: str, token_dir: str):
        self.email = email
        self.credentials_file = credentials_file
        self.token_path = os.path.join(token_dir, f"{email}.json")
        os.makedirs(token_dir, exist_ok=True)
        self._service = None

    # ------------------------------------------------------------------ auth
    def authorize(self, interactive: bool = True):
        """Load cached creds or run the consent flow. Returns the service."""
        creds: Optional[Credentials] = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        if creds and creds.valid:
            pass
        elif creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif interactive:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file, SCOPES
            )
            # login_hint nudges Google to pre-select the right account.
            creds = flow.run_local_server(
                port=0, login_hint=self.email, prompt="consent"
            )
        else:
            raise RuntimeError(
                f"No valid token for {self.email}; run `auth` for this account first."
            )

        with open(self.token_path, "w") as fh:
            fh.write(creds.to_json())
        self._service = build("gmail", "v1", credentials=creds)
        return self._service

    @property
    def service(self):
        if self._service is None:
            self.authorize(interactive=False)
        return self._service

    # ------------------------------------------------------------------ send
    def send(self, to: str, subject: str, body: str,
             from_name: Optional[str] = None,
             in_reply_to: Optional[str] = None,
             references: Optional[str] = None,
             thread_id: Optional[str] = None) -> dict:
        msg = MIMEText(body)
        msg["To"] = to
        msg["From"] = formataddr((from_name, self.email)) if from_name else self.email
        msg["Subject"] = subject
        msg["Message-ID"] = make_msgid()
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
            msg["References"] = references or in_reply_to

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        payload = {"raw": raw}
        if thread_id:
            payload["threadId"] = thread_id
        return (
            self.service.users()
            .messages()
            .send(userId="me", body=payload)
            .execute()
        )

    # -------------------------------------------------------------- receiver
    def find_warmup_messages(self, pool_addresses: list[str], newer_than_days: int = 2):
        """Unread messages from other pool members, in inbox OR spam."""
        senders = " OR ".join(f"from:{a}" for a in pool_addresses if a != self.email)
        query = f"({senders}) is:unread newer_than:{newer_than_days}d in:anywhere"
        resp = (
            self.service.users()
            .messages()
            .list(userId="me", q=query, maxResults=50)
            .execute()
        )
        return resp.get("messages", [])

    def get_message(self, msg_id: str) -> dict:
        return (
            self.service.users()
            .messages()
            .get(userId="me", id=msg_id, format="metadata",
                 metadataHeaders=["Subject", "Message-ID", "References", "From"])
            .execute()
        )

    def engage(self, msg_id: str, star: bool = True):
        """The reputation-building move: pull out of spam, mark read, star.

        Removing SPAM and adding no-longer-unread is the single most valuable
        signal — it teaches Google's filter this sender belongs in the inbox.
        """
        add = ["INBOX"]
        remove = ["SPAM", "UNREAD"]
        if star:
            add.append("STARRED")
        self.service.users().messages().modify(
            userId="me", id=msg_id,
            body={"addLabelIds": add, "removeLabelIds": remove},
        ).execute()

    def header(self, message: dict, name: str) -> Optional[str]:
        for h in message.get("payload", {}).get("headers", []):
            if h["name"].lower() == name.lower():
                return h["value"]
        return None
