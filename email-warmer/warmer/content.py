"""Natural-looking message content.

Warming mail should read like real, low-volume human correspondence: varied
subjects, short bodies, occasional threading. The point is not to fool a person
but to avoid the templated, identical-every-time footprint that spam filters
learn to recognize.
"""

import random

SUBJECTS = [
    "Quick question about {topic}",
    "Following up on {topic}",
    "Notes from today",
    "Re: {topic}",
    "Thoughts on {topic}?",
    "{topic} — draft for review",
    "Can you take a look at this?",
    "Update on {topic}",
    "Scheduling for next week",
    "{topic} recap",
]

TOPICS = [
    "the roadmap", "the Q3 numbers", "the client call", "the onboarding doc",
    "the pricing model", "the design review", "the vendor list", "the demo",
    "the release plan", "the budget", "the hiring loop", "the analytics",
]

OPENERS = [
    "Hey,", "Hi,", "Morning,", "Hello,", "Thanks for the note —",
]

BODIES = [
    "Wanted to circle back on {topic}. Let me know if the current plan still works for you.",
    "Had a few thoughts on {topic} — nothing urgent, happy to chat whenever.",
    "Pulled together a rough draft covering {topic}. Would value your read on it.",
    "Quick one: are we still good for the timeline we discussed on {topic}?",
    "Sharing the latest on {topic}. Flag anything that looks off.",
    "Appreciate you looking at {topic} earlier. Follow-ups below when you have a sec.",
    "Let's lock in next steps for {topic} before end of week.",
]

REPLIES = [
    "Sounds good — thanks for the update.",
    "Got it, this works for me. Talk soon.",
    "Perfect, appreciate the quick turnaround.",
    "Makes sense. I'll take a closer look and get back to you.",
    "Thanks! Nothing else from my side for now.",
    "Great, let's go with that.",
    "Noted — I'll follow up if anything changes.",
]

SIGNOFFS = ["Best,", "Thanks,", "Cheers,", "Talk soon,", "Regards,"]


def new_message(sender_name: str) -> tuple[str, str]:
    topic = random.choice(TOPICS)
    subject = random.choice(SUBJECTS).format(topic=topic)
    body = "\n\n".join([
        random.choice(OPENERS),
        random.choice(BODIES).format(topic=topic),
        f"{random.choice(SIGNOFFS)}\n{sender_name}",
    ])
    return subject, body


def reply_body(sender_name: str) -> str:
    return "\n\n".join([
        random.choice(REPLIES),
        f"{random.choice(SIGNOFFS)}\n{sender_name}",
    ])
