# Roadmap

## Shipped

- **`email-warmer/`** — self-hosted Gmail/Workspace domain warming bot.
  **PAUSED** — development stopped per request; code left in place.
- **`outreach-agent/`** — drafts segmented emails (customers / prospects /
  investors) + a blog post from raw work notes and sends approved ones via
  Resend. Staged-draft-first: nothing sends without explicit approval.
- **`progress-bot/`** — tracks activity in 4xRoads/midnyt-pipeline and writes
  daily/weekly progress updates. Deployed as two scheduled Routines in this
  environment: daily at 12PM ET, weekly Friday 9AM ET.

## Next on the outreach agent

- **Auto-ingest the source material** instead of hand-writing `notes.md`: pull
  from a Claude Code session summary, git log, or a running work journal so
  "summarize what Claude Code and I did" happens without manual note-taking.
- **Approval UX** — a lightweight review step (web page or CLI diff) before send,
  with per-recipient personalization tokens.
- **Scheduling** — recurring digest (e.g. weekly progress email) via a cron/
  trigger, still gated on approval.
- **Contact/segment management** — pull recipient lists from a CRM instead of
  static config.
- **Deliverability tie-in** — send from the warmed `midnyt.ai` domain once the
  warming bot has established reputation, closing the loop between the two tools.

## Next on the warming product (if commercialized)

See `email-warmer/PRICING.md` for the pricing decision and the "unlimited" flag,
and the multi-tenant architecture note in the session history: a seller product
needs per-customer OAuth vaults, a cross-tenant matching engine, and abuse
controls.
