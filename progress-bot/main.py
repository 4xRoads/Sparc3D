#!/usr/bin/env python3
"""Progress bot — summarize repo activity into a daily or weekly update.

Commands:
    daily    Summarize the last `daily_days` of activity.
    weekly   Summarize the last `weekly_days` of activity.

Each run: collects git activity, writes the update with the Claude API, saves a
markdown report file, and (if RESEND_API_KEY is set) emails it.
"""

import argparse
import os
import sys

import yaml

from collect import gather, to_prompt_text
from notify import email, write_report
from report import write_update

HERE = os.path.dirname(os.path.abspath(__file__))


def load_cfg(path: str) -> dict:
    with open(path) as fh:
        return yaml.safe_load(fh)


def run(cadence: str, cfg: dict) -> None:
    days = cfg["daily_days"] if cadence == "daily" else cfg["weekly_days"]
    activity = gather(cfg["repo_path"], days)
    print(f"[{cadence}] {activity['commit_count']} commit(s) in last {days}d",
          file=sys.stderr)

    update = write_update(
        cfg["project"], to_prompt_text(activity), cadence, cfg["model"]
    )

    reports_dir = cfg["reports_dir"]
    if not os.path.isabs(reports_dir):
        reports_dir = os.path.join(HERE, reports_dir)
    path = write_report(reports_dir, cadence, update.title, update.summary_markdown)
    print(f"Report: {path}")

    subject = f"[{cadence.capitalize()}] {update.title}"
    sent = email(cfg["from"], cfg.get("to", []), subject, update.summary_markdown)
    print("Emailed." if sent else "Email skipped (RESEND_API_KEY unset or no recipients).")


def main():
    p = argparse.ArgumentParser(description="Progress bot")
    p.add_argument("cadence", choices=["daily", "weekly"])
    p.add_argument("-c", "--config", default=os.path.join(HERE, "config.yaml"))
    args = p.parse_args()
    run(args.cadence, load_cfg(args.config))


if __name__ == "__main__":
    main()
