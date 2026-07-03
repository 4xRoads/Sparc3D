# Email Warming Bot (Gmail / Google Workspace)

A small, self-hosted bot that warms the sending reputation of a domain — here
`midnyt.ai` — by generating realistic, low-volume, two-way email traffic among a
pool of mailboxes you control. It sends varied messages on a slowly increasing
schedule, and on the receiving side it rescues those messages from spam, marks
them read, stars them, and replies to a fraction. Those engagement signals are
what actually teach Gmail that your domain belongs in the inbox.

> **Use it only on mailboxes you own or are authorized to manage.** This is a
> deliverability tool for your own domain, not a cold-outreach or bulk sender.

## Before you touch the bot: fix your DNS

Warming does nothing if your domain isn't authenticated. In Google Admin +
your DNS provider, confirm all three:

- **SPF** — `v=spf1 include:_spf.google.com ~all`
- **DKIM** — enable in Google Admin → Apps → Gmail → Authenticate email, publish the key
- **DMARC** — start at `v=DMARC1; p=none; rua=mailto:you@midnyt.ai`

Skipping this is the #1 reason warming fails.

## How it works

1. **Ramp** (`warmer/schedule.py`) — starts at ~4 emails/day across the pool and
   grows 25%/day up to a 40/day ceiling (see the curve below). Slow and steady is
   the entire point; a cold domain that blasts volume looks like a spammer.
2. **Send** (`warmer/engine.py`) — picks random sender→recipient pairs from the
   pool, composes varied natural content (`warmer/content.py`), and spaces sends
   with random human-like gaps.
3. **Engage** — each mailbox scans for unread mail from other pool members
   (including anything that landed in spam), pulls it into the inbox, marks it
   read + starred, and replies ~35% of the time to create two-way threads.

```
day  pool emails/day
  0        4
  3        8
  7       20
 14       40  (steady state)
```

## Setup

1. **Google Cloud project + OAuth client**
   - console.cloud.google.com → new project → enable the **Gmail API**.
   - Credentials → Create OAuth client ID → **Desktop app** → download as
     `credentials.json` into this folder.
   - On the OAuth consent screen add each mailbox as a **Test user** (or publish
     the app). For Workspace domains an admin can trust the client instead.

2. **Install + configure**
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp config.example.yaml config.yaml   # then edit accounts + ramp
   ```

3. **Authorize each mailbox once** (opens a browser per account):
   ```bash
   python main.py auth
   ```

4. **Preview, then run:**
   ```bash
   python main.py run --dry-run   # log-only, sends nothing
   python main.py status          # today's target + pool info
   python main.py run             # one real pass
   python main.py daemon          # one pass/day, continuously
   ```

Deploy `daemon` on any always-on box (a $5 VPS, a home server, a free-tier VM)
or wrap `run` in a daily cron job.

## Best practices baked in

- Start small, grow gradually, cap the ceiling.
- Randomized pairs, content, and send timing — no robotic footprint.
- Real spam-rescue + reply signals, not just raw sends.
- Warm for **4–8 weeks** before real outreach; keep a lower background volume
  running afterward so the reputation doesn't decay.

---

## What will this cost?

Building and running this bot is essentially free — the real costs are the
mailboxes and a place to run it.

| Item | Cost | Notes |
|------|------|-------|
| The bot itself | **$0** | This repo; Gmail API is free within quota |
| Gmail API usage | **$0** | Warming volume is nowhere near the free 1B units/day |
| Google Workspace mailbox (`midnyt.ai`) | **~$7/mo each** | Business Starter, per user. Free Gmail accounts cost $0 but don't warm *your* domain |
| Peer mailboxes for the pool | **$0–7/mo each** | Free `@gmail.com` accounts work fine as peers |
| Hosting for the daemon | **$0–6/mo** | Free-tier VM, or a $5 VPS (DigitalOcean/Hetzner) |

**Realistic monthly total for warming `midnyt.ai`:**
- Bare-bones (1 Workspace mailbox + free Gmail peers + free-tier host): **~$7/mo**
- Comfortable (2–3 Workspace mailboxes + $5 VPS): **~$20–30/mo**

**One-time:** a few hours of your setup (DNS + Google Cloud OAuth). No dev cost.

### How that compares to buying a service

Commercial warmup tools (Warmup Inbox, Instantly, Lemwarm/Lemlist, Mailwarm)
run roughly **$15–40 per inbox per month**. They give you a large ready-made peer
network — which warms faster than a 3–4 mailbox pool — and a dashboard, at the
cost of a subscription and handing engagement control to a third party.

**Rule of thumb:** for a single domain and a handful of mailboxes you control,
this self-hosted bot at ~$7–30/mo is the cheaper path. If you need to warm many
inboxes quickly or want the bigger peer network and reporting, a paid service is
usually worth the money.
