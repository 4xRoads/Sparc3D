"""Minimal Resend send wrapper."""

from __future__ import annotations

import os

import requests

RESEND_ENDPOINT = "https://api.resend.com/emails"


def send_email(sender: str, to: list[str], subject: str, text: str) -> dict:
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not set in the environment.")
    resp = requests.post(
        RESEND_ENDPOINT,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={"from": sender, "to": to, "subject": subject, "text": text},
        timeout=30,
    )
    if resp.status_code >= 300:
        raise RuntimeError(f"Resend error {resp.status_code}: {resp.text}")
    return resp.json()
