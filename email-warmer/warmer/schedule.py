"""Volume ramp for a warming domain.

The whole game is a slow, steady increase. Blast 200 emails on day one from a
cold domain and you look exactly like a spammer. Start with a handful and grow
a bounded percentage per day, capping at a sustainable steady-state volume.
"""

from __future__ import annotations

import math
from datetime import date


def daily_target(start_date: date, start_volume: int, growth: float,
                 max_per_day: int, today: date | None = None) -> int:
    """Emails the *whole pool* should send today.

    start_volume: emails on day 0 (e.g. 4)
    growth:       fractional daily increase (e.g. 0.25 == +25%/day)
    max_per_day:  steady-state ceiling (e.g. 40)
    """
    today = today or date.today()
    days = max(0, (today - start_date).days)
    target = start_volume * ((1 + growth) ** days)
    return int(min(max_per_day, math.ceil(target)))


def per_account_cap(target: int, num_accounts: int) -> int:
    """Rough ceiling per mailbox so no single account sends the whole quota."""
    if num_accounts <= 1:
        return target
    return max(1, math.ceil(target / num_accounts) + 1)
