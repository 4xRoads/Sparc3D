# Pricing

## Current plan

| Plan  | Price        | Inboxes    |
|-------|--------------|------------|
| Basic | $7.99 / mo   | up to 3    |
| Pro   | $15 / mo     | unlimited  |

Per-inbox marginal cost is ~$0.15–0.50/mo (customers bring their own mailboxes;
OAuth sends are free), so both tiers are high-margin at normal usage.

## ⚠️ Flag on "unlimited"

"Unlimited inboxes at $15" is the one number worth revisiting. A warming
network carries real per-inbox load — every inbox sends/receives daily and
consumes matching orchestration. No competitor offers unlimited inboxes for a
flat fee, and the reason is agencies: one agency connecting 300–500 inboxes on
the $15 plan turns a 90%-margin product into a loss leader (~$75–125/mo infra +
network burden for $15 revenue), and they're exactly the buyers who will find
this pricing.

Safer shapes that keep the simple two-tier feel:

- **Pro = "up to 25 inboxes," then $X/inbox beyond.** Keeps $15 as the headline;
  meters only the heavy accounts.
- **Fair-use cap** on Pro (e.g. 50 inboxes) with an Agency tier above it.
- Keep unlimited, but **rate-limit total network volume per account** so a
  500-inbox account can't consume 500 inboxes' worth of throughput.

Recommend shipping with a soft cap + "contact us for agency volume" rather than
literally unlimited. Easy to loosen later; painful to tighten after launch.
