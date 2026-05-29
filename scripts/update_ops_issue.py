#!/usr/bin/env python3
"""Create or update the weekly repository ops issue."""

from __future__ import annotations

import datetime as dt
import argparse
import os
import sys
from pathlib import Path

from triage_submission_prs import (
    GitHub,
    bounty_claims,
    dashboard,
    pr_files_by_number,
    submission_data_by_pr,
    triage_pr,
)


MARKER = "<!-- ergo-bounties-ops-status -->"
TITLE = "Ergo Bounties Ops Status"
ROOT = Path(__file__).resolve().parents[1]


def file_age_hours(path: Path) -> float | None:
    if not path.exists():
        return None
    return (dt.datetime.now(dt.UTC).timestamp() - path.stat().st_mtime) / 3600


def health_summary(results: list[dict], payment_queue: str) -> list[str]:
    counts = {
        "open_submission_prs": len(results),
        "invalid": sum("invalid-submission" in r["labels"] for r in results),
        "stale": sum("stale-reservation" in r["labels"] for r in results),
        "waiting_upstream": sum("upstream-unmerged" in r["labels"] for r in results),
        "ready_review": sum("ready-review" in r["labels"] for r in results),
        "payment_ready": sum("payment-ready" in r["labels"] for r in results),
    }
    data_age = file_age_hours(ROOT / "data" / "all.md")
    queue_items = payment_queue.count("\n| ") - 1 if "| Contributor |" in payment_queue else 0

    lines = [
        f"- Open submission PRs: {counts['open_submission_prs']}",
        f"- Invalid: {counts['invalid']}",
        f"- Stale: {counts['stale']}",
        f"- Waiting upstream: {counts['waiting_upstream']}",
        f"- Ready review: {counts['ready_review']}",
        f"- Payment queue: {max(queue_items, 0)}",
    ]
    if data_age is None:
        lines.append("- Data freshness: `data/all.md` missing")
    else:
        state = "ok" if data_age < 30 else "stale"
        lines.append(f"- Data freshness: {state} ({data_age:.1f} hours old)")
    return lines


def upsert_ops_issue(gh: GitHub, body: str) -> None:
    issues = gh.get_all(f"/repos/{gh.repo}/issues?state=open")
    existing = next((item for item in issues if item["title"] == TITLE), None)
    if existing:
        gh.request("PATCH", f"/repos/{gh.repo}/issues/{existing['number']}", {"body": body})
    else:
        gh.request("POST", f"/repos/{gh.repo}/issues", {"title": TITLE, "body": body})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print issue body without writing GitHub issue")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY", "ErgoDevs/Ergo-Bounties")
    if not token:
        print("GITHUB_TOKEN or GH_TOKEN is required", file=sys.stderr)
        return 2

    gh = GitHub(repo, token)
    prs = gh.get_all(f"/repos/{repo}/pulls?state=open")
    files_by_pr = pr_files_by_number(gh, prs)
    submissions = submission_data_by_pr(gh, prs, files_by_pr)
    claims = bounty_claims(submissions)
    results = [triage_pr(gh, pr, submissions[pr["number"]], claims, files_by_pr.get(pr["number"], [])) for pr in prs]

    queue_path = ROOT / "submissions" / "payment_queue.md"
    payment_queue = queue_path.read_text(encoding="utf-8") if queue_path.exists() else "Payment queue missing.\n"

    body = "\n".join(
        [
            MARKER,
            f"Updated: {dt.datetime.now(dt.UTC).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## Health",
            "",
            *health_summary(results, payment_queue),
            "",
            "## Submission Dashboard",
            "",
            dashboard(results),
            "",
            "## Payment Queue",
            "",
            payment_queue,
        ]
    )
    if args.dry_run:
        print(body)
        return 0
    upsert_ops_issue(gh, body)
    print(f"Updated ops issue: {TITLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
