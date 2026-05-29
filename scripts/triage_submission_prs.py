#!/usr/bin/env python3
"""Triage Ergo-Bounties submission pull requests."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import re
import sys
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


VALID_STATUSES = {"in-progress", "awaiting-review", "reviewed", "paid"}
PLACEHOLDERS = {"", "YOUR_GITHUB_USERNAME", "YOUR_WALLET_ADDRESS", "YOUR_CONTACT_INFO"}
MARKER = "<!-- ergo-bounties-submission-triage -->"
LABELS = {
    "invalid-json": "d73a4a",
    "missing-wallet": "d73a4a",
    "upstream-unmerged": "fbca04",
    "ready-review": "0e8a16",
    "payment-ready": "5319e7",
    "stale-reservation": "d93f0b",
    "invalid-submission": "d73a4a",
    "duplicate-bounty": "fbca04",
}
LABEL_DESCRIPTIONS = {
    "invalid-json": "Submission JSON cannot be parsed",
    "missing-wallet": "Submission has no real wallet address",
    "upstream-unmerged": "Linked work PR is not merged yet",
    "ready-review": "Submission is ready for reviewer verification",
    "payment-ready": "Reviewed submission appears ready for payment",
    "stale-reservation": "Reservation passed expected completion",
    "invalid-submission": "Submission has blocking validation issues",
    "duplicate-bounty": "Another open PR claims same bounty",
}


class GitHub:
    def __init__(self, repo: str, token: str) -> None:
        self.repo = repo
        self.token = token

    def request(self, method: str, path: str, data: Any | None = None) -> Any:
        body = None if data is None else json.dumps(data).encode()
        req = Request(
            f"https://api.github.com{path}",
            data=body,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "Ergo-Bounties-submission-triage",
            },
        )
        if body is not None:
            req.add_header("Content-Type", "application/json")
        with urlopen(req, timeout=30) as response:
            if response.status == 204:
                return None
            return json.loads(response.read().decode())

    def get_all(self, path: str) -> list[Any]:
        out: list[Any] = []
        page = 1
        while True:
            sep = "&" if "?" in path else "?"
            chunk = self.request("GET", f"{path}{sep}per_page=100&page={page}")
            if not chunk:
                return out
            out.extend(chunk)
            if len(chunk) < 100:
                return out
            page += 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "ErgoDevs/Ergo-Bounties"))
    parser.add_argument("--pr", type=int, help="Only triage one pull request")
    parser.add_argument("--comment", action="store_true", help="Create/update a triage comment on --pr")
    parser.add_argument("--apply-labels", action="store_true", help="Apply triage labels")
    parser.add_argument("--close-invalid", action="store_true", help="Close invalid submission PRs")
    parser.add_argument("--close-stale", action="store_true", help="Close stale/invalid PRs after grace period")
    parser.add_argument("--stale-grace-days", type=int, default=14)
    parser.add_argument("--write-dashboard", default="", help="Write markdown dashboard")
    parser.add_argument("--request-reviewer", action="store_true", help="Request/tag original issue author")
    parser.add_argument("--exit-zero", action="store_true", help="Exit 0 even when triage findings exist")
    return parser.parse_args()


def github_pr_url(value: str) -> tuple[str, str, int] | None:
    parsed = urlparse(value)
    match = re.fullmatch(r"/([^/]+)/([^/]+)/pull/(\d+)", parsed.path)
    if parsed.netloc.lower() != "github.com" or not match:
        return None
    return match.group(1), match.group(2), int(match.group(3))


def md_text(value: object) -> str:
    """Escape user-controlled text for GitHub markdown output."""
    return (
        str(value)
        .replace("\r", " ")
        .replace("\n", " ")
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def normalize_bounty_id(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    parsed = github_issue_url(raw)
    if parsed:
        owner, repo, number = parsed
        return f"{owner.lower()}/{repo.lower()}#{number}"
    match = re.fullmatch(r"([^/\s]+)/([^#\s]+)#(\d+)", raw)
    if match:
        owner, repo, number = match.groups()
        return f"{owner.lower()}/{repo.lower()}#{number}"
    return raw.lower()


def read_submission(gh: GitHub, path: str, sha: str, raw_url: str = "") -> tuple[dict[str, Any] | None, str | None]:
    try:
        if raw_url:
            req = Request(raw_url, headers={"User-Agent": "Ergo-Bounties-submission-triage"})
            with urlopen(req, timeout=30) as response:
                raw = response.read().decode()
        else:
            content = gh.request("GET", f"/repos/{gh.repo}/contents/{path}?ref={sha}")
            raw = base64.b64decode(content["content"]).decode()
        return json.loads(raw), None
    except Exception as exc:  # noqa: BLE001 - user-facing validation error
        return None, f"cannot parse JSON: {exc}"


def github_issue_url(value: str) -> tuple[str, str, int] | None:
    parsed = urlparse(value)
    match = re.fullmatch(r"/([^/]+)/([^/]+)/(?:issues|pull)/(\d+)", parsed.path)
    if parsed.netloc.lower() != "github.com" or not match:
        return None
    return match.group(1), match.group(2), int(match.group(3))


def issue_author(gh: GitHub, value: str) -> str:
    parsed = github_issue_url(value)
    if not parsed:
        return ""
    owner, repo, number = parsed
    try:
        issue = gh.request("GET", f"/repos/{owner}/{repo}/issues/{number}")
        return issue["user"]["login"]
    except HTTPError:
        return ""


def submission_labels(data: dict[str, Any], issues: list[str], linked_merged: bool | None) -> set[str]:
    labels: set[str] = set()
    status = str(data.get("status", "")).lower()
    joined = "\n".join(issues)
    if "cannot parse JSON" in joined:
        labels.add("invalid-json")
    if "wallet_address" in joined:
        labels.add("missing-wallet")
    if "not merged" in joined:
        labels.add("upstream-unmerged")
    if "expired" in joined:
        labels.add("stale-reservation")
    if "duplicate" in joined:
        labels.add("duplicate-bounty")
    fatal_words = ("missing", "placeholder", "invalid", "must be", "does not match", "expected one of")
    if any(word in joined for word in fatal_words):
        labels.add("invalid-submission")
    if not issues and status == "awaiting-review" and linked_merged is True:
        labels.add("ready-review")
    if not issues and status == "reviewed":
        labels.add("payment-ready")
    return labels


def validate_submission(
    gh: GitHub,
    pr: dict[str, Any],
    file_path: str,
    data: dict[str, Any],
    bounty_claims: dict[str, list[int]],
) -> tuple[list[str], set[str], str, bool | None, str, dt.date | None]:
    issues: list[str] = []
    required = [
        "contributor",
        "wallet_address",
        "work_link",
        "work_title",
        "payment_currency",
        "bounty_value",
        "status",
        "submission_date",
    ]
    status = str(data.get("status", "")).lower()
    linked_merged: bool | None = None
    reviewer = issue_author(gh, str(data.get("original_issue_link", "")).strip())
    expected_date: dt.date | None = None

    for key in required:
        value = data.get(key)
        if key == "work_link" and status == "in-progress":
            continue
        if str(value or "").strip() in PLACEHOLDERS:
            issues.append(f"`{key}` is missing or still a placeholder")

    if "original_issue_link" in data and not github_issue_url(str(data.get("original_issue_link", ""))):
        issues.append("`original_issue_link` must be a GitHub issue or PR URL")

    if not isinstance(data.get("bounty_value"), (int, float)) or data.get("bounty_value", 0) <= 0:
        issues.append("`bounty_value` must be a positive number")

    if status not in VALID_STATUSES:
        issues.append(f"`status` is `{data.get('status')}`, expected one of {', '.join(sorted(VALID_STATUSES))}")

    expected = str(data.get("expected_completion", "")).strip()
    if status == "in-progress" and expected:
        try:
            expected_date = dt.date.fromisoformat(expected)
            if expected_date < dt.date.today():
                issues.append(f"in-progress reservation expired on `{expected}`")
        except ValueError:
            issues.append("`expected_completion` is not YYYY-MM-DD")

    submission_date = str(data.get("submission_date", "")).strip()
    if submission_date:
        try:
            dt.date.fromisoformat(submission_date)
        except ValueError:
            issues.append("`submission_date` is not YYYY-MM-DD")

    work_link = str(data.get("work_link", "")).strip()
    if work_link:
        parsed = github_pr_url(work_link)
        if not parsed:
            issues.append("`work_link` must be a GitHub pull request URL")
        else:
            owner, repo, number = parsed
            try:
                linked = gh.request("GET", f"/repos/{owner}/{repo}/pulls/{number}")
                linked_merged = bool(linked.get("merged"))
                if status in {"awaiting-review", "reviewed", "paid"} and not linked.get("merged"):
                    issues.append(f"linked work PR `{owner}/{repo}#{number}` is not merged")
                if linked.get("state") == "closed" and not linked.get("merged"):
                    issues.append(f"linked work PR `{owner}/{repo}#{number}` closed unmerged")
            except HTTPError as exc:
                issues.append(f"cannot fetch linked work PR `{owner}/{repo}#{number}`: HTTP {exc.code}")
    elif status in {"awaiting-review", "reviewed", "paid"}:
        issues.append("`work_link` is missing or still a placeholder")

    if status == "paid":
        if not str(data.get("payment_tx_id", "")).strip():
            issues.append("`paid` submissions require `payment_tx_id`")
        if not str(data.get("payment_date", "")).strip():
            issues.append("`paid` submissions require `payment_date`")

    if status == "reviewed" and not reviewer:
        issues.append("reviewer could not be inferred from `original_issue_link`")

    if str(data.get("contributor", "")).strip().lower() != pr["user"]["login"].lower():
        issues.append(f"`contributor` does not match PR author `{pr['user']['login']}`")

    bounty_id = normalize_bounty_id(str(data.get("bounty_id", "")).strip())
    if not bounty_id:
        bounty_id = normalize_bounty_id(str(data.get("original_issue_link", "")).strip())
    duplicates = [n for n in bounty_claims.get(bounty_id, []) if n != pr["number"]]
    if bounty_id and duplicates:
        issues.append(f"duplicate bounty claim also open in PR(s): {', '.join(f'#{n}' for n in duplicates)}")

    prefixed = [f"{file_path}: {issue}" for issue in issues]
    return prefixed, submission_labels(data, prefixed, linked_merged), bounty_id, linked_merged, reviewer, expected_date


def pr_files_by_number(gh: GitHub, prs: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    return {pr["number"]: gh.get_all(f"/repos/{gh.repo}/pulls/{pr['number']}/files") for pr in prs}


def submission_data_by_pr(
    gh: GitHub,
    prs: list[dict[str, Any]],
    files_by_pr: dict[int, list[dict[str, Any]]] | None = None,
) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, list[dict[str, Any]]] = {}
    files_by_pr = files_by_pr or pr_files_by_number(gh, prs)
    for pr in prs:
        entries: list[dict[str, Any]] = []
        for item in files_by_pr.get(pr["number"], []):
            path = item["filename"]
            if path.startswith("submissions/") and path.endswith(".json"):
                data, error = read_submission(gh, path, pr["head"]["sha"], item.get("raw_url", ""))
                entries.append({"path": path, "data": data, "error": error})
        out[pr["number"]] = entries
    return out


def bounty_claims(submissions: dict[int, list[dict[str, Any]]]) -> dict[str, list[int]]:
    claims: dict[str, list[int]] = {}
    for pr_number, entries in submissions.items():
        for entry in entries:
            data = entry.get("data") or {}
            bounty_id = normalize_bounty_id(str(data.get("bounty_id", "")).strip())
            if not bounty_id:
                bounty_id = normalize_bounty_id(str(data.get("original_issue_link", "")).strip())
            if bounty_id:
                claims.setdefault(bounty_id, []).append(pr_number)
    return claims


def select_prs_to_triage(
    all_open_prs: list[dict[str, Any]],
    submissions: dict[int, list[dict[str, Any]]],
    pr_number: int | None,
) -> list[dict[str, Any]]:
    """For scheduled runs, triage only PRs that actually edit submissions."""
    if pr_number:
        return [pr for pr in all_open_prs if pr["number"] == pr_number]
    return [pr for pr in all_open_prs if submissions.get(pr["number"])]


def triage_pr(
    gh: GitHub,
    pr: dict[str, Any],
    submissions: list[dict[str, Any]],
    claims: dict[str, list[int]],
    files: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if files is None:
        files = gh.get_all(f"/repos/{gh.repo}/pulls/{pr['number']}/files")
    issues: list[str] = []
    labels: set[str] = set()
    bounty_ids: list[str] = []
    reviewers: set[str] = set()
    expired_dates: list[dt.date] = []
    if not submissions:
        issues.append("no changed `submissions/*.json` file")
        labels.add("invalid-submission")

    for entry in submissions:
        path, data, error = entry["path"], entry.get("data"), entry.get("error")
        if error:
            issues.append(f"{path}: {error}")
            labels.update({"invalid-json", "invalid-submission"})
        elif isinstance(data, dict):
            new_issues, new_labels, bounty_id, _linked_merged, reviewer, expected_date = validate_submission(
                gh, pr, path, data, claims
            )
            issues.extend(new_issues)
            labels.update(new_labels)
            if bounty_id:
                bounty_ids.append(bounty_id)
            if reviewer:
                reviewers.add(reviewer)
            if expected_date:
                expired_dates.append(expected_date)

    changed_non_submission = [
        item["filename"]
        for item in files
        if not item["filename"].startswith("submissions/") and item["filename"] != "submissions/README.md"
    ]
    if changed_non_submission:
        issues.append(f"unexpected non-submission file changes: {', '.join(changed_non_submission[:5])}")
        labels.add("invalid-submission")

    return {
        "number": pr["number"],
        "title": pr["title"],
        "author": pr["user"]["login"],
        "url": pr["html_url"],
        "issues": issues,
        "labels": sorted(labels),
        "bounty_ids": sorted(set(bounty_ids)),
        "reviewers": sorted(reviewers),
        "expired_dates": sorted(expired_dates),
        "state": pr["state"],
    }


def render(results: list[dict[str, Any]]) -> str:
    lines = [MARKER, "### Submission triage"]
    for result in results:
        status = "needs attention" if result["issues"] else "looks valid"
        lines.append(f"- #{result['number']} {status}: {md_text(result['title'])}")
        for issue in result["issues"][:8]:
            lines.append(f"  - {issue}")
        if len(result["issues"]) > 8:
            lines.append(f"  - plus {len(result['issues']) - 8} more issue(s)")
    return "\n".join(lines) + "\n"


def dashboard(results: list[dict[str, Any]]) -> str:
    buckets = [
        ("Ready Review", lambda r: "ready-review" in r["labels"]),
        ("Payment Ready", lambda r: "payment-ready" in r["labels"]),
        ("Waiting Upstream", lambda r: "upstream-unmerged" in r["labels"]),
        ("Stale", lambda r: "stale-reservation" in r["labels"]),
        ("Invalid", lambda r: "invalid-submission" in r["labels"]),
    ]
    lines = [
        "# Submission Triage",
        "",
        f"Generated: {dt.datetime.now(dt.UTC).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
    ]
    for name, predicate in buckets:
        lines.extend([f"## {name}", ""])
        matches = [r for r in results if predicate(r)]
        if not matches:
            lines.extend(["None.", ""])
            continue
        for result in matches:
            labels = ", ".join(result["labels"]) or "none"
            lines.append(f"- [#{result['number']}]({result['url']}) {md_text(result['title'])} ({labels})")
        lines.append("")
    return "\n".join(lines)


def ensure_labels(gh: GitHub) -> None:
    existing = {item["name"] for item in gh.get_all(f"/repos/{gh.repo}/labels")}
    for name, color in LABELS.items():
        if name not in existing:
            gh.request(
                "POST",
                f"/repos/{gh.repo}/labels",
                {"name": name, "color": color, "description": LABEL_DESCRIPTIONS[name]},
            )


def apply_labels(gh: GitHub, result: dict[str, Any]) -> None:
    current = {item["name"] for item in gh.get_all(f"/repos/{gh.repo}/issues/{result['number']}/labels")}
    managed = set(LABELS)
    wanted = set(result["labels"])
    for name in sorted(wanted - current):
        gh.request("POST", f"/repos/{gh.repo}/issues/{result['number']}/labels", {"labels": [name]})
    for name in sorted((current & managed) - wanted):
        gh.request("DELETE", f"/repos/{gh.repo}/issues/{result['number']}/labels/{name}")


def upsert_comment(gh: GitHub, pr_number: int, body: str) -> None:
    comments = gh.get_all(f"/repos/{gh.repo}/issues/{pr_number}/comments")
    existing = next((item for item in comments if MARKER in item.get("body", "")), None)
    if existing:
        gh.request("PATCH", f"/repos/{gh.repo}/issues/comments/{existing['id']}", {"body": body})
    else:
        gh.request("POST", f"/repos/{gh.repo}/issues/{pr_number}/comments", {"body": body})


def request_reviewers_or_tag(gh: GitHub, result: dict[str, Any]) -> None:
    reviewers = [name for name in result["reviewers"] if name.lower() != result["author"].lower()]
    if not reviewers:
        return
    try:
        gh.request("POST", f"/repos/{gh.repo}/pulls/{result['number']}/requested_reviewers", {"reviewers": reviewers})
    except HTTPError:
        upsert_comment(
            gh,
            result["number"],
            render([result]) + "\nReviewer hint: " + ", ".join(f"@{name}" for name in reviewers) + "\n",
        )


def should_close_stale(result: dict[str, Any], grace_days: int) -> bool:
    if "stale-reservation" not in result["labels"]:
        return False
    today = dt.date.today()
    return any((today - expected).days >= grace_days for expected in result["expired_dates"])


def should_close_invalid(result: dict[str, Any]) -> bool:
    labels = set(result["labels"])
    if labels & {"invalid-json", "missing-wallet", "duplicate-bounty"}:
        return True
    fatal_bits = (
        "contributor` does not match",
        "`status` is",
        "`work_link` must be",
        "closed unmerged",
        "unexpected non-submission file changes",
    )
    return any(any(bit in issue for bit in fatal_bits) for issue in result["issues"])


def close_pr(gh: GitHub, result: dict[str, Any], reason: str) -> None:
    upsert_comment(gh, result["number"], render([result]) + f"\nClosing: {reason}.\n")
    gh.request("PATCH", f"/repos/{gh.repo}/pulls/{result['number']}", {"state": "closed"})


def main() -> int:
    args = parse_args()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("GITHUB_TOKEN or GH_TOKEN is required", file=sys.stderr)
        return 2

    gh = GitHub(args.repo, token)
    all_open_prs = gh.get_all(f"/repos/{args.repo}/pulls?state=open")
    files_by_pr = pr_files_by_number(gh, all_open_prs)
    all_submissions = submission_data_by_pr(gh, all_open_prs, files_by_pr)
    if args.pr:
        prs = select_prs_to_triage(all_open_prs, all_submissions, args.pr)
        if not prs:
            prs = [gh.request("GET", f"/repos/{args.repo}/pulls/{args.pr}")]
            all_open_prs.extend(prs)
            files_by_pr.update(pr_files_by_number(gh, prs))
            all_submissions.update(submission_data_by_pr(gh, prs, files_by_pr))
    else:
        prs = select_prs_to_triage(all_open_prs, all_submissions, None)
    submissions = {pr["number"]: all_submissions.get(pr["number"], []) for pr in prs}
    claims = bounty_claims(all_submissions)
    results = [triage_pr(gh, pr, submissions[pr["number"]], claims, files_by_pr.get(pr["number"], [])) for pr in prs]
    body = render(results)
    print(body)

    if args.apply_labels:
        ensure_labels(gh)
        for result in results:
            apply_labels(gh, result)

    if args.comment:
        if not args.pr:
            print("--comment requires --pr", file=sys.stderr)
            return 2
        upsert_comment(gh, args.pr, body)

    if args.request_reviewer:
        for result in results:
            request_reviewers_or_tag(gh, result)

    if args.close_stale:
        for result in results:
            if should_close_stale(result, args.stale_grace_days):
                close_pr(gh, result, "stale reservation exceeded grace period")

    if args.close_invalid:
        for result in results:
            if should_close_invalid(result):
                close_pr(gh, result, "submission has blocking validation failures")

    if args.write_dashboard:
        with open(args.write_dashboard, "w", encoding="utf-8") as handle:
            handle.write(dashboard(results))

    if args.exit_zero:
        return 0
    return 1 if any(result["issues"] for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
