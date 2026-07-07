# Roadmap

## Shipped

- **email warming bot** — self-hosted Gmail/Workspace domain warming bot.
  **PAUSED** and **relocated** to `4xroads/midnyt-pipeline` (branch
  `claude/email-warmer`, `email-warmer/`); no longer in this repo.
- **`outreach-agent/`** — drafts segmented emails (customers / prospects /
  investors) + a blog post from raw work notes and sends approved ones via
  Resend. Staged-draft-first: nothing sends without explicit approval.
- **`progress-bot/`** — tracks activity in 4xRoads/midnyt-pipeline and writes
  daily/weekly progress updates. The **Python version stays here** as the
  portable/local runner. The **deployed version is a Vercel cron** in the
  pipeline repo (`web/app/api/progress/[cadence]/route.ts` + `vercel.json`),
  so all secrets stay in Vercel and Claude Code is out of the runtime path.
  Data source: **option A** — commits via the GitHub API (read-only
  `PROGRESS_GH_TOKEN` in Vercel). Daily 12PM ET, weekly Friday 9AM ET.

## Marketing Progress

A future tracker for **marketing progress** (distinct from the engineering
progress bot, which reads git commits).

- **Option B — Supabase-sourced activity.** Instead of git, source progress from
  the pipeline's own Supabase data the Next app already reads (e.g. ideas
  created, projects committed, deliverables produced, funnel/engagement events).
  Needs **no new secret** — reuses the Supabase creds already in Vercel. Produces
  a marketing/product-activity digest rather than a code-commit digest. Natural
  fit as a second Vercel cron route (`/api/progress/marketing/...`) reusing the
  same branded template and Resend send.
- Candidate metrics to define: new ideas, projects started, deliverables shipped,
  active users, week-over-week deltas.
- Could feed the `outreach-agent` so customer/investor emails cite real
  product-activity numbers.

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

See `email-warmer/PRICING.md` in the midnyt-pipeline repo for the pricing
decision and the "unlimited" flag,
and the multi-tenant architecture note in the session history: a seller product
needs per-customer OAuth vaults, a cross-tenant matching engine, and abuse
controls.
