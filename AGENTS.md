# Agent Instructions

## Communication

- Use `$caveman` style by default: terse, technical, no filler.
- Preserve exact code, commands, paths, errors, and API names.
- Expand only when ambiguity could cause wrong or destructive action.
- Minimize token use. Prefer short status, compact summaries, direct file refs.

## Repo Safety

- Do not print `.env` values or tokens.
- Use `.env` only via environment variables, mainly `GITHUB_TOKEN`.
- Never close, merge, label, comment on, or mutate live GitHub PRs unless user explicitly asks.
- Dry-run first for GitHub automation changes.
- Do not revert user changes. Check `git status --short` before edits.

## Repo Shape

- Bounty data output lives in `data/`.
- Discovery pages: `data/new-bounties.md`, `data/recently-active.md`, `data/stale-bounties.md`, `data/starter-bounties.md`.
- Submission claims live in `submissions/*.json`.
- Submission reports: `submissions/payment_status.md`, `submissions/payment_queue.md`, `submissions/paid.md`, `submissions/triage.md`.
- Submission process docs live in `docs/bounty-submission-guide.md` and `docs/reviewer-guide.md`.
- GitHub Actions live in `.github/workflows/`.
- Automation scripts live in `scripts/`.
- Main updater entrypoint is `run.py`.

## Submission Automation

- Prefer `scripts/triage_submission_prs.py` for PR triage.
- Prefer `scripts/update_ops_issue.py --dry-run` for ops dashboard checks.
- Validate:
  - required fields
  - allowed status: `in-progress`, `awaiting-review`, `reviewed`, `paid`
  - placeholder values like `YOUR_WALLET_ADDRESS`
  - `work_link` is GitHub PR URL
  - linked upstream PR merge state
  - stale `expected_completion`
  - duplicate `bounty_id`
  - payment fields for `paid`
- Keep schema aligned with `.github/submission.schema.json`.
- Keep dashboard output in `submissions/triage.md`.

## Useful Commands

```bash
python3 -m py_compile scripts/triage_submission_prs.py
python3 -m json.tool .github/submission.schema.json >/dev/null
GITHUB_TOKEN="$GITHUB_TOKEN" python3 scripts/triage_submission_prs.py --write-dashboard /tmp/ergo-triage.md
GITHUB_TOKEN="$GITHUB_TOKEN" python3 scripts/update_ops_issue.py --dry-run
python3 -m src.tests.run_bounty_check
./test.sh
```

## Editing Rules

- Use `apply_patch` for manual edits.
- Keep generated data churn small unless task is about generated reports.
- Prefer stdlib Python for repo automation.
- Avoid new dependencies unless payoff is clear.
- Keep GitHub workflow permissions narrow.

## Final Response

- Say what changed.
- Say what was verified.
- Mention any live GitHub writes, or explicitly say none.
