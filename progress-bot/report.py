"""Turn collected activity into a written progress update via the Claude API."""

from __future__ import annotations

import anthropic
from pydantic import BaseModel


class Update(BaseModel):
    title: str
    summary_markdown: str


DAILY_SYSTEM = """You write a founder's daily engineering progress update. Be \
brief and concrete. Group related commits into themes; call out anything shipped \
or merged. Do not pad, do not invent work that isn't in the activity log, and \
don't just relist commit messages verbatim — synthesize. If there was no \
activity, say so plainly in one line."""

WEEKLY_SYSTEM = """You write a founder's weekly engineering progress update. \
Give a narrative of what moved this week: themes, what shipped, what's in \
progress, and a one-line read on velocity using the stats. Ground every claim \
in the activity log; do not invent metrics or work. Keep it skimmable with short \
sections."""

PROMPT = """Project: {project}

Here is the git activity to summarize. Write the update as markdown.

{activity}"""


def write_update(project: str, activity_text: str, cadence: str, model: str) -> Update:
    client = anthropic.Anthropic()
    system = DAILY_SYSTEM if cadence == "daily" else WEEKLY_SYSTEM
    resp = client.messages.parse(
        model=model,
        max_tokens=8000,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{
            "role": "user",
            "content": PROMPT.format(project=project, activity=activity_text),
        }],
        output_format=Update,
    )
    if resp.parsed_output is None:
        raise RuntimeError(f"No parseable update (stop_reason={resp.stop_reason}).")
    return resp.parsed_output
