#!/usr/bin/env python3
"""Render + send a progress update whose prose is supplied (not Claude-generated).

Lets a Claude Code session act as the writer while reusing this repo's collector,
branded template, and Resend sender — so a scheduled run can send the full
branded email with only RESEND_API_KEY set (no ANTHROPIC_API_KEY needed).

    python send_manual.py daily  --title "..." --summary-file summary.md
    python send_manual.py weekly --title "..." --summary-file summary.md
"""

import argparse
import os

import yaml

from collect import gather
from notify import email, write_report
from render import render_email

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cadence", choices=["daily", "weekly"])
    p.add_argument("--title", required=True)
    p.add_argument("--summary-file", required=True)
    p.add_argument("-c", "--config", default=os.path.join(HERE, "config.yaml"))
    args = p.parse_args()

    with open(args.config) as fh:
        cfg = yaml.safe_load(fh)
    with open(args.summary_file) as fh:
        summary_md = fh.read().strip()

    days = cfg["daily_days"] if args.cadence == "daily" else cfg["weekly_days"]
    activity = gather(cfg["repo_path"], days)

    html_body = render_email(args.title, summary_md, args.cadence, activity)

    reports_dir = cfg["reports_dir"]
    if not os.path.isabs(reports_dir):
        reports_dir = os.path.join(HERE, reports_dir)
    path = write_report(reports_dir, args.cadence, args.title, summary_md)
    print(f"Report: {path}")

    subject = f"[{args.cadence.capitalize()}] {args.title}"
    sent = email(cfg["from"], cfg.get("to", []), subject, summary_md, html=html_body)
    if sent:
        print(f"Emailed via Resend. id={sent}")
    else:
        print("Email NOT sent (RESEND_API_KEY unset or no recipients in config).")


if __name__ == "__main__":
    main()
