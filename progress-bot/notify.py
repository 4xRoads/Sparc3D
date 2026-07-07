"""Delivery: always write a local report file; email via Resend if configured."""

from __future__ import annotations

import os
from datetime import date

import requests

RESEND_ENDPOINT = "https://api.resend.com/emails"


def write_report(reports_dir: str, cadence: str, title: str, body_md: str) -> str:
    os.makedirs(reports_dir, exist_ok=True)
    fname = f"{cadence}-{date.today().isoformat()}.md"
    path = os.path.join(reports_dir, fname)
    with open(path, "w") as fh:
        fh.write(f"# {title}\n\n{body_md}\n")
    return path


def email(sender: str, to: list[str], subject: str, text: str,
          html: str | None = None) -> str | None:
    """Best-effort email. Returns the Resend id, or None if not configured.

    Sends the branded HTML when provided, with `text` as the plain-text fallback.
    """
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key or not to:
        return None
    payload = {"from": sender, "to": to, "subject": subject, "text": text}
    if html:
        payload["html"] = html
    resp = requests.post(
        RESEND_ENDPOINT,
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if resp.status_code >= 300:
        raise RuntimeError(f"Resend error {resp.status_code}: {resp.text}")
    return resp.json().get("id")
