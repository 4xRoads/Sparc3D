"""Collect development activity from a local git clone over a time window."""

from __future__ import annotations

import subprocess


def _run(args: list[str]) -> str:
    return subprocess.run(
        args, capture_output=True, text=True, check=False
    ).stdout.strip()


def _default_ref(repo: str) -> str:
    ref = _run(["git", "-C", repo, "rev-parse", "--abbrev-ref", "origin/HEAD"])
    return ref or "origin/master"


def gather(repo: str, since_days: int) -> dict:
    """Return a structured view of activity in the last `since_days` days.

    Best-effort deepens the shallow clone and fetches so history is present at
    runtime; failures (already complete, offline) are non-fatal.
    """
    subprocess.run(
        ["git", "-C", repo, "fetch", "--quiet", "--depth", "500", "origin"],
        capture_output=True, text=True, check=False,
    )
    ref = _default_ref(repo)
    since = f"{since_days} days ago"

    commits_raw = _run([
        "git", "-C", repo, "log", f"--since={since}", "--date=short",
        "--pretty=format:%h\x1f%ad\x1f%an\x1f%s", ref,
    ])
    commits = []
    for line in filter(None, commits_raw.splitlines()):
        h, date, author, subject = (line.split("\x1f") + ["", "", "", ""])[:4]
        commits.append({"hash": h, "date": date, "author": author, "subject": subject})

    # File-change totals from numstat.
    numstat = _run([
        "git", "-C", repo, "log", f"--since={since}", "--numstat",
        "--pretty=format:", ref,
    ])
    added = deleted = 0
    files: set[str] = set()
    for line in filter(None, numstat.splitlines()):
        parts = line.split("\t")
        if len(parts) == 3:
            a, d, path = parts
            added += int(a) if a.isdigit() else 0
            deleted += int(d) if d.isdigit() else 0
            files.add(path)

    prs = [c for c in commits if "Merge pull request" in c["subject"]]

    return {
        "since_days": since_days,
        "commits": commits,
        "commit_count": len(commits),
        "pr_merges": prs,
        "authors": sorted({c["author"] for c in commits if c["author"]}),
        "files_touched": len(files),
        "lines_added": added,
        "lines_deleted": deleted,
    }


def to_prompt_text(activity: dict) -> str:
    """Flatten the activity dict into text for the model."""
    lines = [
        f"Window: last {activity['since_days']} day(s)",
        f"Commits: {activity['commit_count']} | PR merges: {len(activity['pr_merges'])} "
        f"| files touched: {activity['files_touched']} "
        f"| +{activity['lines_added']}/-{activity['lines_deleted']} lines",
        f"Contributors: {', '.join(activity['authors']) or 'n/a'}",
        "",
        "Commits (newest first):",
    ]
    for c in activity["commits"]:
        lines.append(f"  {c['date']} {c['hash']} [{c['author']}] {c['subject']}")
    if not activity["commits"]:
        lines.append("  (no commits in this window)")
    return "\n".join(lines)
