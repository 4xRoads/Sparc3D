# Progress Bot

Tracks development activity in **4xRoads/midnyt-pipeline** and produces a
written **daily** and **weekly** progress update.

Each run:

1. collects git activity over the window (commits, PR merges, files touched,
   lines changed, contributors),
2. writes a concise update with the Claude API (`claude-opus-4-8`),
3. saves a markdown report file, and
4. emails it via Resend if `RESEND_API_KEY` is set (best-effort).

## Deployment (scheduled, in Claude Code on the web)

Two Routines fire fresh autonomous sessions in this environment:

| Cadence | When (Eastern) | Cron (UTC, currently EDT) |
|---------|----------------|----------------------------|
| Daily   | 12:00 PM every day | `0 16 * * *` |
| Weekly  | 9:00 AM Friday     | `0 13 * * 5` |

> **Daylight saving:** the scheduler runs on UTC with no automatic DST. These
> crons are set for **EDT (summer)**. When the US falls back in November, add one
> hour to each (`0 17 * * *` and `0 14 * * 5`) to keep the same wall-clock time.

Each firing clones/fetches the pipeline, runs the collector, composes the
update, and delivers it. **Delivery works with zero extra secrets:** the update
is included in the session's completion notification, which is emailed/pushed to
the account owner. If `ANTHROPIC_API_KEY` and `RESEND_API_KEY` are configured in
the environment, the standalone script path (below) also runs and sends a
branded email from `midnyt.ai`.

## Running it directly (cron on any host)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml   # set repo_path, recipients

export ANTHROPIC_API_KEY=...          # required for the write step
export RESEND_API_KEY=...             # optional; enables email

python main.py daily
python main.py weekly
```

`config.yaml` and everything in `reports/` are gitignored.

## Files

- `collect.py` — git activity gathering (deterministic, no API needed).
- `report.py` — Claude call that writes the update (structured output).
- `notify.py` — writes the report file; best-effort Resend email.
- `main.py` — `daily` / `weekly` entry point.
