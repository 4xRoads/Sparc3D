#!/usr/bin/env python3
"""Email warming bot for Gmail / Google Workspace mailboxes.

Commands:
    auth      One-time OAuth consent for every account in the config.
    run       Do one warming pass (send + engage). Use --dry-run to preview.
    daemon    Run continuously, one pass per day at a randomized time.
    status    Print today's target volume and pool info.

All behavior is driven by config.yaml. See config.example.yaml.
"""

import argparse
import logging
import random
import sys
import time
from datetime import date

import yaml

from warmer import WarmingEngine


def load_cfg(path: str) -> dict:
    with open(path) as fh:
        return yaml.safe_load(fh)


def main():
    p = argparse.ArgumentParser(description="Gmail domain warming bot")
    p.add_argument("command", choices=["auth", "run", "daemon", "status"])
    p.add_argument("-c", "--config", default="config.yaml")
    p.add_argument("--dry-run", action="store_true",
                   help="Log what would happen without sending or modifying mail")
    p.add_argument("--send-only", action="store_true")
    p.add_argument("--engage-only", action="store_true")
    args = p.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    cfg = load_cfg(args.config)
    engine = WarmingEngine(cfg)

    if args.command == "auth":
        engine.authorize_all()
        return

    if args.command == "status":
        for k, v in engine.status().items():
            print(f"{k:>14}: {v}")
        return

    if args.command == "run":
        _one_pass(engine, args)
        return

    if args.command == "daemon":
        log = logging.getLogger("warmer")
        last_run = None
        while True:
            today = date.today()
            if last_run != today:
                # spread the daily pass over working hours
                log.info("Starting daily warming pass for %s", today)
                _one_pass(engine, args)
                last_run = today
            # sleep 20-40 min then re-check the day boundary
            time.sleep(random.uniform(1200, 2400))


def _one_pass(engine: WarmingEngine, args):
    if not args.engage_only:
        engine.run_sends(dry_run=args.dry_run)
    if not args.send_only:
        engine.run_engagement(dry_run=args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
