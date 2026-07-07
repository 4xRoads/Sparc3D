"""Fill the Resend HTML template from an update + activity stats.

Keeps a tiny, dependency-free markdown->inline-HTML converter so the branded
email renders in any client without a CSS-in-<head> reliance.
"""

from __future__ import annotations

import html
import os
import re
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "templates", "progress_email.html")

_H = 'color:#f4f4f8;font-weight:700;margin:20px 0 8px;'
_LINK = "color:#9a8cff;"


def _inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r'<strong style="color:#e8e8f0;">\1</strong>', text)
    text = re.sub(r"`(.+?)`",
                  r'<code style="background:#20202b;padding:1px 5px;border-radius:4px;'
                  r'font-size:13px;color:#c9c9d6;">\1</code>', text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", rf'<a href="\2" style="{_LINK}">\1</a>', text)
    return text


def md_to_html(md: str) -> str:
    """Minimal markdown: #/##/### headings, - and * bullets, 1. lists, paragraphs."""
    out: list[str] = []
    bullets: list[str] = []

    def flush():
        if bullets:
            items = "".join(f'<li style="margin:4px 0;">{b}</li>' for b in bullets)
            out.append(f'<ul style="margin:8px 0 8px 20px;padding:0;">{items}</ul>')
            bullets.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush()
            continue
        m = re.match(r"(#{1,3})\s+(.*)", line)
        if m:
            flush()
            size = {1: 19, 2: 16, 3: 15}[len(m.group(1))]
            out.append(f'<div style="{_H}font-size:{size}px;">{_inline(m.group(2))}</div>')
            continue
        m = re.match(r"[-*]\s+(.*)", line)
        if m:
            bullets.append(_inline(m.group(1)))
            continue
        m = re.match(r"\d+\.\s+(.*)", line)
        if m:
            bullets.append(_inline(m.group(1)))
            continue
        flush()
        out.append(f'<p style="margin:10px 0;">{_inline(line)}</p>')
    flush()
    return "\n".join(out)


def _stat_cell(value: str, label: str) -> str:
    return (
        '<td align="center" style="padding:14px 6px;">'
        f'<div style="font-size:20px;font-weight:700;color:#f4f4f8;">{value}</div>'
        f'<div style="font-size:11px;letter-spacing:1px;text-transform:uppercase;'
        f'color:#6c6c85;margin-top:3px;">{label}</div></td>'
    )


def stats_row(activity: dict) -> str:
    cells = "".join([
        _stat_cell(str(activity.get("commit_count", 0)), "commits"),
        _stat_cell(str(len(activity.get("pr_merges", []))), "PRs"),
        _stat_cell(str(activity.get("files_touched", 0)), "files"),
        _stat_cell(
            f"+{activity.get('lines_added', 0)}/-{activity.get('lines_deleted', 0)}",
            "lines",
        ),
    ])
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="background:#12121a;border:1px solid #262632;border-radius:10px;'
        'margin-top:16px;"><tr>' + cells + "</tr></table>"
    )


def render_email(title: str, summary_md: str, cadence: str, activity: dict) -> str:
    with open(TEMPLATE) as fh:
        tpl = fh.read()
    return (
        tpl.replace("{{cadence}}", cadence.capitalize())
        .replace("{{title}}", html.escape(title))
        .replace("{{date}}", date.today().strftime("%b %d, %Y"))
        .replace("{{stats_row}}", stats_row(activity))
        .replace("{{content}}", md_to_html(summary_md))
    )
