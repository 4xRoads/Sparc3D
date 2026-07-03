# Outreach Agent

Turns raw progress notes — what you and Claude Code have been building and
thinking — into a set of outreach drafts, then sends the ones you approve via
[Resend](https://resend.com).

It produces, in one pass:

- an email tailored to **customers** (what's new, what to try),
- an email tailored to **prospects** (problem + proof + one CTA),
- an email tailored to **investors** (traction and trajectory),
- a **blog post** that leads with the progress.

**Drafting** uses the Claude API (`claude-opus-4-8`) with structured output.
**Sending** uses Resend. Every draft is staged for your review first — the agent
never sends anything without an explicit `send --yes`. It's also instructed not
to invent metrics or facts that aren't in your notes.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml   # edit: from address, brand voice, recipients

export ANTHROPIC_API_KEY=...   # drafting
export RESEND_API_KEY=...       # sending
```

For Resend: verify the `midnyt.ai` domain in your Resend dashboard and set the
`from:` in `config.yaml` to an address on it. (Resend requires the same
SPF/DKIM DNS records as the warming bot — get those in place first.)

## Use

```bash
# 1. Drop your notes in a file — bullet points are fine.
python main.py generate notes.md

# 2. Review what it drafted.
python main.py list
python main.py show email-investors.md

# 3. Send the ones you approve (dry run without --yes).
python main.py send email-customers.md          # preview
python main.py send email-customers.md --yes     # actually send
```

Emails go to the recipient list for their segment in `config.yaml`. The blog
post is left as a markdown file for you to publish wherever you like.

`config.yaml` and everything in `drafts/` are gitignored — notes and generated
copy stay local.

## Notes

- The quality of the output tracks the quality of your notes. Include real
  specifics (what shipped, numbers if you have them, what's next) — the agent
  won't fabricate the parts you leave out.
- Cost is a few cents per `generate` run (one Claude API call) plus Resend's
  per-email pricing (free tier covers low volume). No infrastructure to host.
