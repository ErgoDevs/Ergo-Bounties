# 📡 Bounty Radar

A filterable, single-page browser for the bounties in [`data/all.md`](../data/all.md).

The generated markdown tables are the source of truth and are excellent at being
exact. They are less good at answering "what should I work on?" — you cannot sort
them, filter them to your stack, or see what changed since last week. The Radar
reads the same data and answers that question, with no backend and no build step.

Served from GitHub Pages at `/radar/` once Pages is enabled for this repository.

## What it adds over the markdown tables

- **Radar score (0–100)** — ranks every bounty by reward value (log-scaled), recent
  maintainer attention, competition, and stack accessibility, minus a penalty for
  contested issues. Tap any score and the card shows its own arithmetic — every
  component, its reason, and the board median — so the number is arguable rather
  than authoritative.
- **Money in money** — figures lead in dollars, with the denominated amount
  (`1,000 SigUSD · Σ4,215`) underneath. Dollar-pegged bounties take their pegged
  amount directly instead of round-tripping through the rounded ERG column, which
  was pushing 500 SigUSD bounties to $499.86 and out of a `$500+` filter.
- **What changed** — new, closed/paid, and re-priced bounties over the last 7 or 30
  days, computed against archived snapshots. The board has no history view.
- **Trends** — open-bounty count, total board value, and monthly new-vs-closed flow,
  rendered as dependency-free SVG.
- **Contention detection** — some bounties look ideal and are traps: contributor
  after contributor opens a pull request, none is ever merged, and the bounty stays
  listed because nothing ever closes the issue. A daily sweep reads the PRs linked
  to each bounty issue and flags the ones with work stacked up and nothing merged.
  It also flags issues carrying two contradictory bounty labels.
- **Pipeline & payments** — who is working on what right now, what has been paid
  (with on-chain transaction links), and how long submissions have waited.
- **Filters, watchlist, shareable views** — active filters live in the URL hash, so
  any view is a link. Starred bounties are saved locally in the browser.

## Honest about its own freshness

Different parts of the page come from different passes, and they can disagree. The
↻ button re-reads the board and the exchange rate, but the contention sweep, the
payment pipeline and the trends only move when the daily job runs. Each layer
carries its own date, and the stamp turns amber when they diverge rather than
backdating everything to one reassuring timestamp.

The same rule governs the contention sweep: **a missing warning means "not checked
yet", never "clear"**. The `✓ Nobody on it` filter therefore requires positive
confirmation and switches itself off when there is no sweep data to stand on.

## How it works

```
radar/index.html            the whole app; data embedded between /*NAME_START*/ markers
radar/scripts/parser.js     parses data/all.md into JSON
radar/scripts/archive.js    daily job: read the board → history/YYYY-MM-DD.json
                            → recompute 7/30-day baselines → refresh index.html
radar/scripts/backfill.js   one-off: reseed trends.json from this repo's git history
radar/history/              one JSON snapshot per day + the aggregate trend series
```

The daily job is [`.github/workflows/radar-snapshot.yml`](../.github/workflows/radar-snapshot.yml),
which runs at 02:00 UTC — clear of the 00:00 board regeneration and the 09:00
submission triage. It reads `data/all.md` straight from the checkout rather than
over the network, so it always sees exactly the committed board rather than a
half-updated one.

Run it by hand with:

```bash
node radar/scripts/archive.js          # uses this checkout's data/
GITHUB_TOKEN=... node radar/scripts/archive.js   # also runs the contention sweep
```

Without a token the contention and repo-throughput sweeps are skipped and the
previous results are kept, so the page degrades quietly instead of claiming an
all-clear it did not verify.

## Score caveat

The Radar score is a heuristic to aid discovery, not advice. It is deliberately
transparent so it can be argued with — always read the issue before reserving.
