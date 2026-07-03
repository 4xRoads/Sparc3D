"""Drafting layer — turns a work summary into segmented emails + a blog post.

Uses the Claude API with structured output so the result is a validated object,
not free text we have to parse by hand.
"""

from __future__ import annotations

from typing import List

import anthropic
from pydantic import BaseModel


class Email(BaseModel):
    segment: str        # "customers" | "prospects" | "investors"
    subject: str
    body: str           # plain text / light markdown, ready to send
    rationale: str      # why this framing suits this audience (for your review)


class OutreachBundle(BaseModel):
    emails: List[Email]
    blog_post_title: str
    blog_post_markdown: str


SYSTEM = """You are the founder's writing partner. You turn raw progress notes \
into outreach that sounds like the founder wrote it — specific, honest, and \
free of marketing filler. You never invent metrics, customers, or facts that \
are not in the notes. Concrete beats grand. Short beats long."""

PROMPT_TEMPLATE = """Brand & voice context:
{brand_context}

Below are my raw notes on what I (and Claude Code) have been building and \
thinking about. Turn them into an outreach set.

Produce exactly three emails — one each for the segments "customers", \
"prospects", and "investors" — plus one blog post that leads with the traction \
and progress. Tailor each email:
- customers: what's new/better for them, what to try, a light ask for feedback.
- prospects: the problem it solves and the proof it's working, one clear CTA.
- investors: momentum and trajectory — traction, what it signals, what's next.

Keep emails tight (roughly 120-200 words). Ground every claim in the notes; if \
a number isn't in the notes, don't state one. The blog post can be longer and \
narrative, but same honesty rule.

=== RAW NOTES ===
{summary}
=== END NOTES ==="""


def draft_bundle(summary: str, brand_context: str, model: str) -> OutreachBundle:
    client = anthropic.Anthropic()
    prompt = PROMPT_TEMPLATE.format(brand_context=brand_context, summary=summary)
    response = client.messages.parse(
        model=model,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        output_format=OutreachBundle,
    )
    if response.parsed_output is None:
        raise RuntimeError(
            f"Model did not return a parseable bundle (stop_reason={response.stop_reason})."
        )
    return response.parsed_output
