#!/usr/bin/env python3
"""Flag Ergo-Bounties issues where pull requests pile up but nothing ever merges.

Some bounties look ideal from the listing alone -- clear scope, fair reward,
"good first issue" -- and are traps anyway: contributor after contributor opens
a pull request, none of them is ever merged, and the issue stays open forever
because nothing ever closes it. Comment count does not catch this; linked pull
requests do.

For every open bounty in `data/all.md` this script reads the issue's timeline,
collects the pull requests that cross-reference it, and counts how many are
open vs merged vs closed. An issue with several open, unmerged pull requests
and no recent merge is "contested" and gets flagged in
`data/contested-bounties.md`.

Design notes, mostly about being honest when the sweep goes wrong:

- Read-only against GitHub. Never comments, labels, or closes anything.
- The timeline is paginated. Events come back oldest-first, so reading only
  the first page would drop the most recent cross-references -- precisely on
  the busiest issues, which are the ones most likely to be contested. Missing
  a trap is worse than reporting a doubtful one, so we walk every page.
- Every issue record carries its own `checked` date. An issue absent from
  `items` has never been checked; an issue present with an old `checked` date
  was checked then, not now. Neither is the same as "clear", and the dashboard
  says so rather than implying a clean bill of health.
- A partial sweep (rate limit, network trouble) keeps the previous findings
  for the issues it did not reach this time instead of dropping them, so a bad
  morning cannot quietly empty a report full of known traps. Carried entries
  are shown with the date they were actually observed.
- A merge only clears an issue if it is recent. `cross-referenced` records
  mentions, not fixes, so one merged PR that happened to say "related to #123"
  would otherwise immunise a bounty against ever being flagged again.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MARKER = "<!-- ergo-bounties-contested-bounties -->"
MAX_TIMELINE_PAGES = 20  # 2000 events; a runaway guard, not an expected limit

# `data/all.md`'s "Bounty" cell is `[repo](repo_url)/[title](issue_url)`. Split
# off the repo link first, then match the title link against what is left --
# matching greedily against the whole cell in one regex mis-captures the repo
# link's own `]...(` as part of the title.
BOUNTY_CELL_RE = re.compile(r"^\[([^\]]+)\]\((https://github\.com/([^/)]+)/([^/)]+))\)/(.*)$")
TITLE_LINK_RE = re.compile(r"^\[(.*)\]\((https://github\.com/[^)]+)\)$")
ISSUE_URL_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/issues/(\d+)$")


class RateLimited(Exception):
    """GitHub asked us to back off. Stop the sweep; do not burn the rest of the board."""


class IssueUnavailable(Exception):
    """This one issue could not be read. Skip it; the rest of the sweep is still good."""


class GitHub:
    def __init__(self, token: str, timeout: int = 30) -> None:
        self.token = token
        self.timeout = timeout

    def _get(self, path: str) -> Any:
        req = Request(
            f"https://api.github.com{path}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "Ergo-Bounties-contested-bounties",
            },
        )
        with urlopen(req, timeout=self.timeout) as response:
            return json.loads(response.read().decode())

    def timeline(self, owner: str, repo: str, number: int) -> list[Any]:
        """All timeline events for one issue, following pagination.

        Raises RateLimited (stop everything) or IssueUnavailable (skip this one).
        A 403 is only a rate limit when GitHub says so in the headers: it is
        also what an org's third-party-application restrictions, a SAML
        requirement, an IP allowlist, or a disabled repository return. Treating
        those as a rate limit would stop the sweep at the first such repo, on
        every run, and leave the rest of the board permanently unchecked.
        """
        events: list[Any] = []
        for page in range(1, MAX_TIMELINE_PAGES + 1):
            path = f"/repos/{owner}/{repo}/issues/{number}/timeline?per_page=100&page={page}"
            try:
                chunk = self._get(path)
            except HTTPError as exc:
                if exc.code == 429 or (exc.code == 403 and _is_rate_limited(exc)):
                    raise RateLimited(f"HTTP {exc.code} on {owner}/{repo}#{number}") from exc
                raise IssueUnavailable(f"HTTP {exc.code} on {owner}/{repo}#{number}") from exc
            except (URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError) as exc:
                # DNS, TLS, reset connections, read timeouts, truncated bodies.
                # One flaky request must not discard a sweep already 80 issues deep.
                raise IssueUnavailable(f"{type(exc).__name__} on {owner}/{repo}#{number}: {exc}") from exc
            if not isinstance(chunk, list):
                raise IssueUnavailable(f"unexpected timeline payload for {owner}/{repo}#{number}")
            events.extend(chunk)
            if len(chunk) < 100:
                break
        return events


def _is_rate_limited(exc: HTTPError) -> bool:
    headers = getattr(exc, "headers", None) or {}
    if headers.get("Retry-After"):
        return True
    remaining = headers.get("X-RateLimit-Remaining")
    return remaining is not None and str(remaining).strip() == "0"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Flag bounty issues with stalled, unmerged pull requests")
    parser.add_argument("--input", default="data/all.md", help="Bounty listing to scan")
    parser.add_argument("--write-dashboard", default="data/contested-bounties.md")
    parser.add_argument("--write-json", default="data/contested_bounties.json")
    parser.add_argument("--min-open-prs", type=int, default=2, help="Open, unmerged PRs needed to flag an issue")
    parser.add_argument(
        "--merge-window-days",
        type=int,
        default=180,
        help="A merged PR only clears an issue if it merged within this many days",
    )
    parser.add_argument("--sleep", type=float, default=0.15, help="Delay between API calls (secondary rate limit)")
    parser.add_argument("--limit", type=int, default=0, help="Only sweep the first N issues (0 = no limit)")
    parser.add_argument("--exit-zero", action="store_true", help="Exit 0 even when contested bounties are found")
    return parser.parse_args(argv)


def md_text(value: object) -> str:
    """Escape user-controlled text (issue/PR titles, usernames) for markdown output."""
    return (
        str(value)
        .replace("\r", " ")
        .replace("\n", " ")
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def parse_bounty_rows(all_md_text: str) -> tuple[list[dict[str, Any]], int]:
    """Extract every sweepable bounty from data/all.md.

    Returns (rows, table_row_count). The second value is how many bounty rows
    the table had at all, so the caller can notice a parser regression: rows
    silently dropping to a handful would otherwise produce a confident,
    nearly-empty "nothing contested" report.
    """
    rows: list[dict[str, Any]] = []
    table_rows = 0
    for line in all_md_text.splitlines():
        if not line.startswith("| ["):
            continue
        table_rows += 1
        cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
        if len(cells) < 3:
            continue
        cell_match = BOUNTY_CELL_RE.match(cells[1])
        if not cell_match:
            continue
        repo_url, rest = cell_match.group(2), cell_match.group(5)
        title_match = TITLE_LINK_RE.match(rest)
        title, url = (title_match.group(1), title_match.group(2)) if title_match else (rest, repo_url)
        issue_match = ISSUE_URL_RE.match(url)
        if not issue_match:
            # Reward programs and bounties posted directly on a pull request
            # have no issue timeline to sweep. Not an error.
            continue
        owner, repo, number = issue_match.groups()
        rows.append({
            "owner": owner,
            "repo": repo,
            "number": int(number),
            "title": title,
            "url": url,
            "value": cells[2],
        })
    return rows, table_rows


def prs_from_timeline(events: list[Any]) -> list[dict[str, Any]]:
    """Pure parser: raw `.../timeline` JSON -> deduped, sorted linked-PR records.

    Kept separate from the network call so it can be tested against fixtures.
    Everything is read defensively: GitHub returns stripped-down `source`
    payloads for cross-references originating in repos the token cannot see,
    and one KeyError here would abort the whole sweep.
    """
    by_key: dict[tuple[str, int], dict[str, Any]] = {}
    for event in events if isinstance(events, list) else []:
        if not isinstance(event, dict) or event.get("event") != "cross-referenced":
            continue
        source = (event.get("source") or {}).get("issue")
        if not isinstance(source, dict):
            continue
        pull_request = source.get("pull_request")
        if not isinstance(pull_request, dict):
            continue
        number = source.get("number")
        if not isinstance(number, int):
            continue
        url = source.get("html_url") or ""
        # Cross-references arrive from arbitrary repositories, and PR numbers
        # restart at 1 in every fork. Deduping on the number alone would
        # collapse two distinct open PRs into one and under-count contention.
        repo_match = re.match(r"^https://github\.com/([^/]+/[^/]+)/pull/\d+$", url)
        repo_key = repo_match.group(1) if repo_match else "?"
        merged_at = pull_request.get("merged_at")
        state = "open" if source.get("state") == "open" else ("merged" if merged_at else "closed")
        by_key[(repo_key, number)] = {
            "number": number,
            "repo": repo_key,
            "state": state,
            "author": ((source.get("user") or {}).get("login")),
            "url": url,
            "merged_at": (merged_at or "")[:10] or None,
        }
    return sorted(by_key.values(), key=lambda pr: (pr["repo"], pr["number"]))


def summarize(prs: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "open": sum(1 for pr in prs if pr["state"] == "open"),
        "merged": sum(1 for pr in prs if pr["state"] == "merged"),
        "closed": sum(1 for pr in prs if pr["state"] == "closed"),
    }


def recent_merge(prs: list[dict[str, Any]], today: dt.date, window_days: int) -> str | None:
    """The most recent merge date within the window, if any.

    `cross-referenced` records mentions, not fixes. A pull request merged years
    ago that merely said "related to #123" should not immunise a bounty against
    ever being flagged again -- and since cross-references accumulate over an
    issue's whole life, the oldest bounties would be the most immunised, which
    is exactly backwards.
    """
    best: str | None = None
    for pr in prs:
        if pr["state"] != "merged" or not pr.get("merged_at"):
            continue
        try:
            merged_on = dt.date.fromisoformat(pr["merged_at"])
        except ValueError:
            continue
        if (today - merged_on).days <= window_days and (best is None or pr["merged_at"] > best):
            best = pr["merged_at"]
    return best


def is_contested(record: dict[str, Any], min_open_prs: int) -> bool:
    return record.get("open", 0) >= min_open_prs and not record.get("recent_merge")


def sweep(
    client: Any,
    rows: list[dict[str, Any]],
    min_open_prs: int,
    merge_window_days: int,
    sleep_s: float,
    limit: int,
    today: dt.date,
) -> dict[str, Any]:
    targets = rows[:limit] if limit > 0 else rows
    attempted = len(targets)
    items: dict[str, Any] = {}
    done = 0
    failed = 0
    consecutive_failures = 0
    stopped = False

    for row in targets:
        try:
            events = client.timeline(row["owner"], row["repo"], row["number"])
        except RateLimited as exc:
            print(f"contested-bounties: {exc}, stopping sweep early", file=sys.stderr)
            stopped = True
            break
        except IssueUnavailable as exc:
            failed += 1
            consecutive_failures += 1
            print(f"contested-bounties: skipping {row['url']}: {exc}", file=sys.stderr)
            # Back off on the failure path too. A burst of unthrottled retries
            # is itself a way to trip GitHub's secondary rate limit.
            time.sleep(sleep_s)
            if consecutive_failures >= 8:
                print(
                    f"contested-bounties: {consecutive_failures} consecutive failures, aborting sweep",
                    file=sys.stderr,
                )
                stopped = True
                break
            continue

        consecutive_failures = 0
        prs = prs_from_timeline(events)
        record = {**row, **summarize(prs), "checked": today.isoformat()}
        merged_recently = recent_merge(prs, today, merge_window_days)
        if merged_recently:
            record["recent_merge"] = merged_recently
        if prs:
            record["prs"] = prs[-10:]
        items[row["url"]] = record
        done += 1
        time.sleep(sleep_s)

    return {
        "items": items,
        "swept": done,
        "attempted": attempted,
        "failed": failed,
        # A limit truncates the sweep as surely as a rate limit does; a report
        # covering 5 of 97 bounties must not read as a complete board.
        "partial": stopped or done < attempted or (limit > 0 and limit < len(rows)),
    }


def merge_with_previous(
    fresh_items: dict[str, Any],
    previous: dict[str, Any] | None,
    live_urls: set[str],
) -> tuple[dict[str, Any], int]:
    """Carry forward previous findings for issues this run did not reach.

    Without this, one rate-limited morning replaces a report full of known
    traps with whatever handful of issues got through. Entries whose bounty has
    since left the board are dropped rather than haunting the report forever.
    """
    merged = dict(fresh_items)
    carried = 0
    previous_items = (previous or {}).get("items") or {}
    fallback_date = (previous or {}).get("fetched")
    for url, record in previous_items.items():
        if url in merged or url not in live_urls or not isinstance(record, dict):
            continue
        carried_record = dict(record)
        carried_record.setdefault("checked", fallback_date)
        merged[url] = carried_record
        carried += 1
    return merged, carried


def build_result(
    swept: dict[str, Any],
    previous: dict[str, Any] | None,
    rows: list[dict[str, Any]],
    min_open_prs: int,
    merge_window_days: int,
    today: dt.date,
) -> dict[str, Any]:
    live_urls = {row["url"] for row in rows}
    items, carried = merge_with_previous(swept["items"], previous, live_urls)
    contested = sorted(
        (rec for rec in items.values() if is_contested(rec, min_open_prs)),
        key=lambda rec: (rec.get("open", 0), rec.get("number", 0)),
        reverse=True,
    )
    return {
        "fetched": today.isoformat(),
        "min_open_prs": min_open_prs,
        "merge_window_days": merge_window_days,
        "items": items,
        "contested": [rec["url"] for rec in contested],
        "swept": swept["swept"],
        "attempted": swept["attempted"],
        "failed": swept["failed"],
        "carried": carried,
        "partial": swept["partial"],
    }


def render_dashboard(result: dict[str, Any]) -> str:
    contested = [result["items"][url] for url in result["contested"] if url in result["items"]]
    today = result["fetched"]

    status = f"Swept {result['swept']}/{result['attempted']} open bounty issues this run"
    details = [f"{result.get('failed', 0)} failed"]
    if result.get("carried"):
        details.append(f"{result['carried']} carried over from a previous run")
    status += f" ({', '.join(details)})."
    if result.get("partial"):
        status += " Partial sweep -- the rest of the board was not checked this run."

    lines = [
        MARKER,
        "# Contested Bounties",
        "",
        f"Generated: {today}",
        status,
        "",
        (
            "Some bounties attract pull request after pull request and never merge any of them, "
            "so the issue stays open and keeps looking available. This report flags open bounty "
            f"issues with {result['min_open_prs']}+ open pull requests and no pull request merged "
            f"in the last {result.get('merge_window_days', 180)} days, so you can see the queue "
            "before adding to it."
        ),
        "",
    ]

    if not contested:
        lines.extend(["No contested bounties among the issues checked so far.", ""])
    else:
        lines.append(f"## Contested ({len(contested)})")
        lines.append("")
        for rec in contested:
            value = f" ({md_text(rec['value'])})" if rec.get("value") else ""
            checked = rec.get("checked")
            stale = "" if checked == today else f" _(checked {md_text(checked or 'unknown')})_"
            lines.append(
                f"- [{md_text(rec['owner'])}/{md_text(rec['repo'])}#{rec['number']}]({rec['url']}) "
                f"{md_text(rec['title'])}{value} — {rec.get('open', 0)} open PR(s), "
                f"{rec.get('merged', 0)} merged{stale}"
            )
            for pr in rec.get("prs", []):
                author = f"@{md_text(pr['author'])}" if pr.get("author") else "unknown"
                lines.append(f"  - [#{pr['number']}]({pr.get('url') or rec['url']}) {md_text(pr['state'])} by {author}")
        lines.append("")

    lines.extend([
        "## Notes",
        "",
        (
            "- An issue missing from `data/contested_bounties.json`'s `items` has not been checked yet, "
            "and an issue whose `checked` date is older than this report was checked then, not now. "
            "Neither means clear."
        ),
        (
            "- A pull request that cross-references an issue is not necessarily an attempt to fix it, "
            "so treat the queue below as a prompt to read the issue, not as a verdict."
        ),
        "- Read-only report: nothing here is posted back to GitHub, and no PRs or issues are touched.",
        "",
    ])
    return "\n".join(lines)


def load_previous(path: str) -> dict[str, Any] | None:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("contested-bounties: no GITHUB_TOKEN/GH_TOKEN, sweep skipped", file=sys.stderr)
        return 0

    if args.limit < 0:
        print("contested-bounties: --limit must be >= 0", file=sys.stderr)
        return 2

    try:
        with open(args.input, "r", encoding="utf-8") as handle:
            all_md_text = handle.read()
    except OSError as exc:
        print(f"contested-bounties: cannot read {args.input}: {exc}", file=sys.stderr)
        return 2

    rows, table_rows = parse_bounty_rows(all_md_text)
    dropped = table_rows - len(rows)
    print(f"contested-bounties: {len(rows)} sweepable issues from {table_rows} bounty rows ({dropped} without an issue URL)")
    # Reward programs and PR-hosted bounties legitimately have no issue to
    # sweep, but if most of the table stops parsing that is a format
    # regression, and a near-empty "nothing contested" report would look like
    # good news rather than a broken parser.
    if table_rows and len(rows) < table_rows * 0.5:
        print(
            f"contested-bounties: only {len(rows)}/{table_rows} rows parsed, {args.input} format may have changed",
            file=sys.stderr,
        )
        return 2

    previous = load_previous(args.write_json)
    today = dt.datetime.now(dt.timezone.utc).date()
    swept = sweep(GitHub(token), rows, args.min_open_prs, args.merge_window_days, args.sleep, args.limit, today)

    if swept["swept"] == 0 and swept["attempted"] > 0 and previous:
        # Nothing at all got through. Keep the committed report rather than
        # replacing known traps with an empty page.
        print(
            f"contested-bounties: swept 0/{swept['attempted']}, keeping previous report from {previous.get('fetched')}",
            file=sys.stderr,
        )
        return 0 if args.exit_zero else 1

    result = build_result(swept, previous, rows, args.min_open_prs, args.merge_window_days, today)
    contested_count = len(result["contested"])
    print(
        f"contested-bounties: swept {result['swept']}/{result['attempted']} issues, "
        f"{result['failed']} failed, {result['carried']} carried over; "
        f"{contested_count} contested{' (partial sweep)' if result['partial'] else ''}"
    )

    if args.write_json:
        with open(args.write_json, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
            handle.write("\n")

    if args.write_dashboard:
        with open(args.write_dashboard, "w", encoding="utf-8") as handle:
            handle.write(render_dashboard(result))

    if args.exit_zero:
        return 0
    return 1 if contested_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
