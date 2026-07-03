#!/usr/bin/env python3
"""Outreach agent — draft segmented emails + a blog post from work notes,
review them, then send via Resend.

Commands:
    generate <notes.md>   Draft emails + blog into drafts/ (nothing is sent).
    list                  Show staged drafts.
    show <draft>          Print a draft.
    send <draft>          Send one email draft via Resend to its segment list.
                          Requires --yes to actually send.

Drafting uses ANTHROPIC_API_KEY; sending uses RESEND_API_KEY. Emails are always
staged for your review first — the agent never sends without an explicit send.
"""

import argparse
import glob
import os
import sys

import yaml

from agent import draft_bundle
from resend_client import send_email

HERE = os.path.dirname(os.path.abspath(__file__))
DRAFTS = os.path.join(HERE, "drafts")


def load_cfg(path: str) -> dict:
    with open(path) as fh:
        return yaml.safe_load(fh)


def _slug(text: str) -> str:
    keep = "".join(c if c.isalnum() else "-" for c in text.lower())
    return "-".join(filter(None, keep.split("-")))[:60]


def _write_draft(name: str, front: dict, body: str) -> str:
    os.makedirs(DRAFTS, exist_ok=True)
    path = os.path.join(DRAFTS, name)
    with open(path, "w") as fh:
        fh.write("---\n")
        yaml.safe_dump(front, fh, sort_keys=False)
        fh.write("---\n\n")
        fh.write(body)
    return path


def _read_draft(path: str) -> tuple[dict, str]:
    with open(path) as fh:
        content = fh.read()
    if content.startswith("---\n"):
        _, fm, body = content.split("---\n", 2)
        return yaml.safe_load(fm) or {}, body.lstrip("\n")
    return {}, content


def cmd_generate(args, cfg):
    with open(args.notes) as fh:
        summary = fh.read()
    print(f"Drafting from {args.notes} with {cfg['model']} ...", file=sys.stderr)
    bundle = draft_bundle(summary, cfg.get("brand_context", ""), cfg["model"])

    segments = cfg.get("segments", {})
    for email in bundle.emails:
        front = {
            "type": "email",
            "segment": email.segment,
            "subject": email.subject,
            "to": segments.get(email.segment, []),
            "rationale": email.rationale,
        }
        name = f"email-{email.segment}.md"
        _write_draft(name, front, email.body)
        print(f"  wrote drafts/{name}  ({len(front['to'])} recipient(s))")

    blog_name = f"blog-{_slug(bundle.blog_post_title)}.md"
    _write_draft(
        blog_name,
        {"type": "blog", "title": bundle.blog_post_title},
        bundle.blog_post_markdown,
    )
    print(f"  wrote drafts/{blog_name}")
    print("\nReview them, then `send` the emails you approve.")


def cmd_list(args, cfg):
    paths = sorted(glob.glob(os.path.join(DRAFTS, "*.md")))
    if not paths:
        print("No drafts. Run `generate` first.")
        return
    for p in paths:
        front, _ = _read_draft(p)
        kind = front.get("type", "?")
        extra = front.get("subject") or front.get("title") or ""
        to = front.get("to", [])
        tag = f" -> {len(to)} recipient(s)" if kind == "email" else ""
        print(f"{os.path.basename(p):32} [{kind}]{tag}  {extra}")


def cmd_show(args, cfg):
    front, body = _read_draft(os.path.join(DRAFTS, args.draft))
    print(yaml.safe_dump(front, sort_keys=False))
    print("-" * 60)
    print(body)


def cmd_send(args, cfg):
    path = os.path.join(DRAFTS, args.draft)
    front, body = _read_draft(path)
    if front.get("type") != "email":
        print("Only email drafts can be sent.", file=sys.stderr)
        sys.exit(1)
    to = front.get("to", [])
    if not to:
        print("No recipients for this segment (check config.yaml).", file=sys.stderr)
        sys.exit(1)

    print(f"Segment : {front.get('segment')}")
    print(f"Subject : {front.get('subject')}")
    print(f"From    : {cfg['from']}")
    print(f"To      : {', '.join(to)}")
    print("-" * 60)
    print(body[:500] + ("..." if len(body) > 500 else ""))
    print("-" * 60)

    if not args.yes:
        print("Dry run. Re-run with --yes to actually send.")
        return
    result = send_email(cfg["from"], to, front["subject"], body)
    print(f"Sent. Resend id: {result.get('id')}")


def main():
    p = argparse.ArgumentParser(description="Outreach agent")
    p.add_argument("-c", "--config", default=os.path.join(HERE, "config.yaml"))
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate"); g.add_argument("notes")
    sub.add_parser("list")
    s = sub.add_parser("show"); s.add_argument("draft")
    sd = sub.add_parser("send"); sd.add_argument("draft")
    sd.add_argument("--yes", action="store_true", help="Actually send (default is dry run)")

    args = p.parse_args()
    cfg = load_cfg(args.config)
    {
        "generate": cmd_generate,
        "list": cmd_list,
        "show": cmd_show,
        "send": cmd_send,
    }[args.command](args, cfg)


if __name__ == "__main__":
    main()
