# Maintainer Runbook

Use this when the repo needs care without changing the public bounty flow.

## Routine Checks

- Daily bounty refresh: `.github/workflows/update-bounties.yml`, scheduled at `00:00 UTC`.
- Submission triage: `.github/workflows/triage-submission-prs.yml`, on PR events and daily at `09:00 UTC`.
- Ops status: `.github/workflows/ops-status.yml`, weekly on Monday at `09:30 UTC`.
- Payment reports: `submissions/payment_status.md`, `submissions/payment_queue.md`, and `submissions/paid.md` are generated from `submissions/*.json`.

## Local Commands

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
./test.sh
```

For a live refresh with a GitHub token in `.env`:

```bash
./scripts/run_live_update.sh
```

For read-only automation checks:

```bash
python scripts/triage_submission_prs.py --dry-run --repo ErgoDevs/Ergo-Bounties
python scripts/update_ops_issue.py --dry-run --repo ErgoDevs/Ergo-Bounties
```

## Source Files

Edit these:

- `src/config/tracked_repos.json`
- `src/config/tracked_orgs.json`
- `src/config/extra_bounties.json`
- `submissions/*.json`
- `src/**`
- `docs/**`

Do not hand-edit these generated files:

- `data/*.md`
- `data/by_language/*.md`
- `data/by_currency/*.md`
- `data/by_org/*.md`
- `submissions/payment_status.md`
- `submissions/payment_queue.md`
- `submissions/paid.md`
- README badges and latest-update marker

Fix generated output by changing source inputs or generator code, then regenerate and validate.

## Bounty Data Rules

- A bounty needs owner, repo, title, URL, amount, currency, status, and stable issue ID.
- Manual bounties live in `src/config/extra_bounties.json`; use `Ongoing` or `Not specified` only when there is no fixed amount.
- Submission reservations should use `owner/repo#issue` in `bounty_id`.
- Placeholder submissions are ignored by the generator and should not reserve real work.
- If bounty totals jump unexpectedly, inspect `data/summary.md`, `data/all.md`, currency rates, and recent upstream labels before patching anything.

## Safety Notes

- Never print GitHub tokens or `.env` contents.
- Workflows install from `requirements.txt`; keep dependency changes centralized there.
- `triage_submission_prs.py` may label/comment/request reviewers. Scheduled runs can close stale or invalid submission PRs; PR event runs are conservative.
- Legacy scripts under `scripts/` and network probes under `src/tests/check_apis.py` are manual tools, not default CI.
