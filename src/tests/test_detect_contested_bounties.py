import datetime as dt

import pytest

from scripts.detect_contested_bounties import (
    GitHub,
    IssueUnavailable,
    RateLimited,
    build_result,
    is_contested,
    md_text,
    merge_with_previous,
    parse_bounty_rows,
    prs_from_timeline,
    recent_merge,
    render_dashboard,
    summarize,
    sweep,
)

TODAY = dt.date(2026, 8, 11)

SAMPLE_ROW = (
    "| [ergoplatform](by_org/ergoplatform.md) | "
    "[sigmastate-interpreter](https://github.com/ergoplatform/sigmastate-interpreter)/"
    "[Finish SigmaMap implementation](https://github.com/ergoplatform/sigmastate-interpreter/issues/1067) | "
    "1000 SigUSD (~Σ4215) | 486d | 283d | 2 | [Scala](by_language/scala.md) | [Reserve](#) |"
)
HEADER = "|Organisation|Bounty|Value|Age|Updated|Comments|Primary Language|Reserve|\n|---|---|---|---|---|---|---|---|\n"


def xref(number, state, *, merged_at=None, repo="o/r", author="alice", is_pr=True):
    source = {"number": number, "state": state, "user": {"login": author}, "html_url": f"https://github.com/{repo}/pull/{number}"}
    if is_pr:
        source["pull_request"] = {"merged_at": merged_at}
    return {"event": "cross-referenced", "source": {"issue": source}}


def row(url="https://github.com/o/r/issues/1", number=1, title="Trap issue"):
    return {"owner": "o", "repo": "r", "number": number, "title": title, "url": url, "value": "500 ERG"}


class FakeClient:
    """Stands in for GitHub. Each entry is either an event list or an exception to raise."""

    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def timeline(self, owner, repo, number):
        self.calls.append((owner, repo, number))
        result = self.responses.get(number, [])
        if isinstance(result, Exception):
            raise result
        return result


# --- row parsing -------------------------------------------------------------

def test_parse_bounty_rows_extracts_owner_repo_number_title():
    rows, table_rows = parse_bounty_rows(HEADER + SAMPLE_ROW + "\n")

    assert table_rows == 1
    assert rows == [{
        "owner": "ergoplatform",
        "repo": "sigmastate-interpreter",
        "number": 1067,
        "title": "Finish SigmaMap implementation",
        "url": "https://github.com/ergoplatform/sigmastate-interpreter/issues/1067",
        "value": "1000 SigUSD (~Σ4215)",
    }]


def test_parse_bounty_rows_counts_unsweepable_rows_separately():
    """PR-hosted bounties have no issue timeline, but must still count as table rows.

    The caller uses the ratio to detect a format regression; if unsweepable
    rows vanished from the denominator, a broken parser would look healthy.
    """
    pr_row = (
        "| [ergoplatform](by_org/ergoplatform.md) | "
        "[ergo](https://github.com/ergoplatform/ergo)/"
        "[Some work](https://github.com/ergoplatform/ergo/pull/2249) | "
        "10 ERG | 5d | 5d | 0 | [Scala](by_language/scala.md) | [Reserve](#) |"
    )
    rows, table_rows = parse_bounty_rows(HEADER + SAMPLE_ROW + "\n" + pr_row + "\n")

    assert len(rows) == 1
    assert table_rows == 2


def test_parse_bounty_rows_ignores_prose_and_malformed_rows():
    text = "# All Open Bounties\n\nSome prose.\n" + HEADER + "| [no bounty cell] | one |\n"
    rows, table_rows = parse_bounty_rows(text)
    assert rows == []
    assert table_rows == 1


# --- timeline parsing --------------------------------------------------------

def test_prs_from_timeline_classifies_open_merged_closed():
    events = [
        {"event": "commented"},
        xref(1, "open"),
        xref(2, "closed", merged_at="2026-01-01T00:00:00Z", author="bob"),
        xref(3, "closed", author="carol"),
        xref(4, "open", is_pr=False),  # a plain issue cross-reference, not a PR
    ]

    prs = prs_from_timeline(events)

    assert [(pr["number"], pr["state"]) for pr in prs] == [(1, "open"), (2, "merged"), (3, "closed")]
    assert summarize(prs) == {"open": 1, "merged": 1, "closed": 1}


def test_prs_from_timeline_keys_on_repo_and_number():
    """Two open PRs numbered 12 in different repos are two PRs, not one.

    PR numbers restart at 1 in every fork, so deduping on the number alone
    under-counts contention and can un-flag a genuinely contested issue.
    """
    prs = prs_from_timeline([xref(12, "open", repo="a/one"), xref(12, "open", repo="b/two")])

    assert summarize(prs)["open"] == 2


def test_prs_from_timeline_dedupes_repeated_events_for_one_pr():
    prs = prs_from_timeline([
        xref(5, "open", repo="o/r"),
        xref(5, "closed", merged_at="2026-02-02T00:00:00Z", repo="o/r"),
    ])

    assert len(prs) == 1
    assert prs[0]["state"] == "merged"


@pytest.mark.parametrize("events", [
    [],
    None,
    ["not-a-dict"],
    [{"event": "cross-referenced", "source": None}],
    [{"event": "cross-referenced", "source": {"issue": {"pull_request": {}}}}],           # no number
    [{"event": "cross-referenced", "source": {"issue": {"number": 1, "pull_request": None}}}],
    [{"event": "cross-referenced", "source": {"issue": {"number": "x", "pull_request": {}}}}],
])
def test_prs_from_timeline_tolerates_stripped_payloads(events):
    """GitHub returns partial `source` objects for cross-refs from invisible repos.

    A KeyError here would escape the per-issue handler and abort the sweep.
    """
    assert prs_from_timeline(events) == []


# --- contested classification -----------------------------------------------

def test_recent_merge_only_counts_merges_inside_the_window():
    fresh = [{"state": "merged", "merged_at": "2026-07-01"}]
    ancient = [{"state": "merged", "merged_at": "2020-01-01"}]

    assert recent_merge(fresh, TODAY, 180) == "2026-07-01"
    assert recent_merge(ancient, TODAY, 180) is None
    assert recent_merge([{"state": "open", "merged_at": None}], TODAY, 180) is None


def test_is_contested_requires_open_threshold_and_no_recent_merge():
    assert is_contested({"open": 2}, min_open_prs=2) is True
    assert is_contested({"open": 1}, min_open_prs=2) is False
    assert is_contested({"open": 3, "recent_merge": "2026-07-01"}, min_open_prs=2) is False
    # An ancient merged mention must not immunise the issue forever.
    assert is_contested({"open": 3, "merged": 1}, min_open_prs=2) is True


def test_md_text_escapes_markdown_control_characters():
    assert md_text("bad | [title]\nnext") == "bad \\| \\[title\\] next"


# --- sweep behaviour ---------------------------------------------------------

def test_sweep_records_checked_date_and_flags_contested():
    client = FakeClient({1: [xref(10, "open"), xref(11, "open", repo="o/r2")]})

    result = sweep(client, [row()], min_open_prs=2, merge_window_days=180, sleep_s=0, limit=0, today=TODAY)

    record = result["items"]["https://github.com/o/r/issues/1"]
    assert record["open"] == 2
    assert record["checked"] == "2026-08-11"
    assert result["partial"] is False


def test_sweep_skips_one_unavailable_issue_and_keeps_the_rest():
    """A single 404/permission failure must not cost the whole sweep."""
    client = FakeClient({1: IssueUnavailable("HTTP 404"), 2: [xref(10, "open")]})
    rows = [row(url="u1", number=1), row(url="u2", number=2)]

    result = sweep(client, rows, min_open_prs=2, merge_window_days=180, sleep_s=0, limit=0, today=TODAY)

    assert result["swept"] == 1
    assert result["failed"] == 1
    assert "u2" in result["items"] and "u1" not in result["items"]
    assert result["partial"] is True


def test_sweep_stops_on_rate_limit_and_keeps_what_it_has():
    client = FakeClient({1: [xref(10, "open")], 2: RateLimited("HTTP 429"), 3: [xref(11, "open")]})
    rows = [row(url="u1", number=1), row(url="u2", number=2), row(url="u3", number=3)]

    result = sweep(client, rows, min_open_prs=2, merge_window_days=180, sleep_s=0, limit=0, today=TODAY)

    assert result["swept"] == 1
    assert client.calls == [("o", "r", 1), ("o", "r", 2)]  # stopped, did not try #3
    assert result["partial"] is True


def test_sweep_aborts_after_consecutive_failures_but_a_success_resets_the_counter():
    rows = [row(url=f"u{i}", number=i) for i in range(1, 12)]
    responses = {1: [xref(1, "open")]}
    responses.update({i: IssueUnavailable("HTTP 500") for i in range(2, 12)})

    result = sweep(FakeClient(responses), rows, min_open_prs=2, merge_window_days=180, sleep_s=0, limit=0, today=TODAY)

    assert result["swept"] == 1
    assert result["failed"] == 8  # aborted at 8 consecutive, not after all 10
    assert result["partial"] is True


def test_sweep_with_limit_reports_itself_as_partial():
    """A --limit 1 smoke test must never publish a clean bill of health for the board."""
    rows = [row(url=f"u{i}", number=i) for i in range(1, 4)]
    client = FakeClient({i: [] for i in range(1, 4)})

    result = sweep(client, rows, min_open_prs=2, merge_window_days=180, sleep_s=0, limit=1, today=TODAY)

    assert result["swept"] == 1
    assert result["attempted"] == 1
    assert result["partial"] is True
    assert len(client.calls) == 1


# --- carry-forward and rendering --------------------------------------------

def test_merge_with_previous_carries_unswept_issues_and_drops_departed_ones():
    fresh = {"u1": {"open": 2, "checked": "2026-08-11"}}
    previous = {"fetched": "2026-08-01", "items": {"u2": {"open": 3}, "u3": {"open": 4}}}

    merged, carried = merge_with_previous(fresh, previous, live_urls={"u1", "u2"})

    assert carried == 1
    assert merged["u2"]["checked"] == "2026-08-01"  # stamped with when it was really seen
    assert "u3" not in merged  # bounty left the board; do not haunt the report


def test_build_result_keeps_known_traps_visible_after_a_partial_sweep():
    """Regression guard: a rate-limited run must not empty a report full of traps."""
    previous = {
        "fetched": "2026-08-01",
        "items": {f"u{i}": {"owner": "o", "repo": "r", "number": i, "title": "t", "url": f"u{i}", "open": 3, "merged": 0} for i in range(2, 12)},
    }
    swept = {"items": {"u1": {"owner": "o", "repo": "r", "number": 1, "title": "t", "url": "u1", "open": 2, "merged": 0, "checked": "2026-08-11"}},
             "swept": 1, "attempted": 11, "failed": 0, "partial": True}
    rows = [row(url=f"u{i}", number=i) for i in range(1, 12)]

    result = build_result(swept, previous, rows, min_open_prs=2, merge_window_days=180, today=TODAY)

    assert len(result["contested"]) == 11  # 1 fresh + 10 carried, not 1
    assert result["carried"] == 10


def test_render_dashboard_marks_partial_sweeps_and_stale_entries():
    result = {
        "fetched": "2026-08-11", "min_open_prs": 2, "merge_window_days": 180,
        "items": {
            "https://github.com/o/r/issues/1": {
                "owner": "o", "repo": "r", "number": 1, "title": "Trap issue",
                "url": "https://github.com/o/r/issues/1", "value": "500 ERG",
                "open": 2, "merged": 0, "checked": "2026-08-01",
                "prs": [{"number": 10, "state": "open", "author": "alice", "url": "https://github.com/o/r/pull/10"}],
            },
        },
        "contested": ["https://github.com/o/r/issues/1"],
        "swept": 1, "attempted": 5, "failed": 1, "carried": 1, "partial": True,
    }

    out = render_dashboard(result)

    assert "o/r#1" in out and "Trap issue" in out and "@alice" in out
    assert "2 open PR(s), 0 merged" in out
    assert "Partial sweep" in out
    assert "carried over from a previous run" in out
    assert "_(checked 2026-08-01)_" in out
    assert "has not been checked yet" in out


def test_render_dashboard_never_claims_a_clean_board():
    result = {"fetched": "2026-08-11", "min_open_prs": 2, "merge_window_days": 180, "items": {},
              "contested": [], "swept": 5, "attempted": 5, "failed": 0, "carried": 0, "partial": False}

    out = render_dashboard(result)

    assert "among the issues checked so far" in out


# --- rate-limit classification ----------------------------------------------

@pytest.mark.parametrize("code,headers,expected", [
    (429, {}, RateLimited),
    (403, {"X-RateLimit-Remaining": "0"}, RateLimited),
    (403, {"Retry-After": "60"}, RateLimited),
    # A permission 403 (org app restrictions, SAML, IP allowlist) is one bad
    # repo, not a reason to abandon the board on every future run.
    (403, {"X-RateLimit-Remaining": "4999"}, IssueUnavailable),
    (403, {}, IssueUnavailable),
    (404, {}, IssueUnavailable),
    (410, {}, IssueUnavailable),
])
def test_timeline_distinguishes_rate_limits_from_per_repo_failures(monkeypatch, code, headers, expected):
    from urllib.error import HTTPError

    def boom(*_args, **_kwargs):
        raise HTTPError("https://api.github.com", code, "nope", headers, None)

    monkeypatch.setattr("scripts.detect_contested_bounties.urlopen", boom)

    with pytest.raises(expected):
        GitHub("token").timeline("o", "r", 1)


def test_timeline_follows_pagination_so_busy_issues_are_not_truncated():
    """Timeline events come back oldest-first.

    Reading only page 1 of a very active issue would drop the most recent
    cross-references -- on exactly the issues most likely to be contested.
    """
    pages = {1: [{"event": "commented"}] * 100, 2: [xref(7, "open"), xref(8, "open")]}
    calls = []

    class PagedGitHub(GitHub):
        def _get(self, path):
            calls.append(path)
            page = int(path.rsplit("page=", 1)[1])
            return pages.get(page, [])

    events = PagedGitHub("token").timeline("o", "r", 1)

    assert len(calls) == 2
    assert summarize(prs_from_timeline(events))["open"] == 2
