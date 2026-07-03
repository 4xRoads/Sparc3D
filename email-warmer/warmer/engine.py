"""Orchestrates one warming pass across the account pool."""

from __future__ import annotations

import logging
import random
import time
from datetime import date, datetime

from . import content, schedule
from .gmail_client import GmailClient

log = logging.getLogger("warmer")


class WarmingEngine:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.accounts = cfg["accounts"]
        self.addresses = [a["email"] for a in self.accounts]
        creds = cfg["credentials_file"]
        token_dir = cfg.get("token_dir", "tokens")
        self.clients = {
            a["email"]: GmailClient(a["email"], creds, token_dir)
            for a in self.accounts
        }
        self.names = {a["email"]: a.get("name", a["email"].split("@")[0])
                      for a in self.accounts}
        self.start_date = _parse_date(cfg["ramp"]["start_date"])

    # ----------------------------------------------------------------- auth
    def authorize_all(self):
        for email, client in self.clients.items():
            log.info("Authorizing %s ...", email)
            client.authorize(interactive=True)
        log.info("All %d accounts authorized.", len(self.clients))

    # --------------------------------------------------------------- sending
    def _today_target(self) -> int:
        r = self.cfg["ramp"]
        return schedule.daily_target(
            self.start_date, r["start_volume"], r["growth"], r["max_per_day"]
        )

    def run_sends(self, dry_run: bool = False) -> int:
        target = self._today_target()
        log.info("Daily send target for the pool: %d", target)
        sent = 0
        sent_by_account: dict[str, int] = {a: 0 for a in self.addresses}
        cap = schedule.per_account_cap(target, len(self.addresses))

        pairs = self._pick_pairs(target)
        for sender, recipient in pairs:
            if sent_by_account[sender] >= cap:
                continue
            subject, body = content.new_message(self.names[sender])
            if dry_run:
                log.info("[dry-run] %s -> %s | %s", sender, recipient, subject)
            else:
                try:
                    self.clients[sender].send(
                        to=recipient, subject=subject, body=body,
                        from_name=self.names[sender],
                    )
                    log.info("sent %s -> %s | %s", sender, recipient, subject)
                except Exception as e:  # keep the pass alive on a single failure
                    log.error("send failed %s -> %s: %s", sender, recipient, e)
                    continue
                self._human_pause()
            sent += 1
            sent_by_account[sender] += 1
        log.info("Sent %d/%d messages this pass.", sent, target)
        return sent

    def _pick_pairs(self, n: int) -> list[tuple[str, str]]:
        pairs = []
        for _ in range(n):
            sender = random.choice(self.addresses)
            recipient = random.choice([a for a in self.addresses if a != sender])
            pairs.append((sender, recipient))
        random.shuffle(pairs)
        return pairs

    # ------------------------------------------------------------- receiving
    def run_engagement(self, dry_run: bool = False) -> int:
        """Rescue warming mail from spam, mark read/star, reply to a fraction."""
        reply_rate = self.cfg.get("reply_rate", 0.3)
        newer = self.cfg["ramp"].get("scan_days", 2)
        engaged = 0
        for email, client in self.clients.items():
            try:
                msgs = client.find_warmup_messages(self.addresses, newer)
            except Exception as e:
                log.error("scan failed for %s: %s", email, e)
                continue
            for m in msgs:
                if dry_run:
                    log.info("[dry-run] %s would engage msg %s", email, m["id"])
                    engaged += 1
                    continue
                try:
                    client.engage(m["id"])
                    engaged += 1
                    if random.random() < reply_rate:
                        self._reply(client, m["id"])
                    self._human_pause(short=True)
                except Exception as e:
                    log.error("engage failed for %s msg %s: %s", email, m["id"], e)
        log.info("Engaged with %d warming messages.", engaged)
        return engaged

    def _reply(self, client: GmailClient, msg_id: str):
        full = client.get_message(msg_id)
        sender = client.header(full, "From") or ""
        subject = client.header(full, "Subject") or ""
        orig_id = client.header(full, "Message-ID")
        refs = client.header(full, "References")
        to_addr = _extract_addr(sender)
        if not to_addr:
            return
        reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"
        client.send(
            to=to_addr,
            subject=reply_subject,
            body=content.reply_body(self.names.get(client.email, "")),
            from_name=self.names.get(client.email),
            in_reply_to=orig_id,
            references=(f"{refs} {orig_id}".strip() if refs else orig_id),
            thread_id=full.get("threadId"),
        )
        log.info("%s replied to %s", client.email, to_addr)

    # ----------------------------------------------------------------- utils
    def _human_pause(self, short: bool = False):
        lo, hi = (5, 25) if short else self.cfg.get("send_gap_seconds", [30, 240])
        time.sleep(random.uniform(lo, hi))

    def status(self) -> dict:
        return {
            "date": date.today().isoformat(),
            "day": (date.today() - self.start_date).days,
            "pool_size": len(self.addresses),
            "target_today": self._today_target(),
            "accounts": self.addresses,
        }


def _parse_date(s: str) -> date:
    return datetime.strptime(str(s), "%Y-%m-%d").date()


def _extract_addr(header_value: str) -> str:
    if "<" in header_value and ">" in header_value:
        return header_value.split("<", 1)[1].split(">", 1)[0].strip()
    return header_value.strip()
