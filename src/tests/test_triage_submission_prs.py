import base64
from urllib.error import HTTPError

import scripts.triage_submission_prs as triage
from scripts.triage_submission_prs import (
    bounty_claims,
    md_text,
    normalize_bounty_id,
    read_submission,
    select_prs_to_triage,
    should_close_invalid,
)


def test_scheduled_triage_selects_only_submission_prs():
    prs = [{"number": 1}, {"number": 2}]
    submissions = {1: [], 2: [{"path": "submissions/example.json"}]}

    selected = select_prs_to_triage(prs, submissions, None)

    assert selected == [{"number": 2}]


def test_missing_submission_pr_is_not_auto_closed():
    result = {
        "labels": ["invalid-submission"],
        "issues": ["no changed `submissions/*.json` file"],
    }

    assert should_close_invalid(result) is False


def test_bounty_ids_are_normalized_for_duplicate_claims():
    submissions = {
        1: [{"data": {"bounty_id": "Owner/Repo#12"}}],
        2: [{"data": {"bounty_id": "https://github.com/owner/repo/issues/12"}}],
    }

    assert normalize_bounty_id("Owner/Repo#12") == "owner/repo#12"
    assert bounty_claims(submissions) == {"owner/repo#12": [1, 2]}


def test_markdown_text_escapes_user_controlled_output():
    assert md_text("bad | [title]\nnext") == "bad \\| \\[title\\] next"


def test_download_failure_falls_back_to_authenticated_contents_at_head_sha(monkeypatch):
    calls = []

    def fail_raw(*args, **kwargs):
        raise HTTPError("https://raw.example", 504, "Gateway Time-out", {}, None)

    class FakeGitHub:
        repo = "ErgoDevs/Ergo-Bounties"
        token = "secret"

        def request(self, method, path):
            calls.append((method, path))
            return {"content": base64.b64encode(b'{"status":"in-progress"}').decode()}

    monkeypatch.setattr(triage, "urlopen", fail_raw)
    data, error = read_submission(FakeGitHub(), "submissions/x.json", "abc123", "https://raw.example/x", "fork/repo")

    assert data == {"status": "in-progress"}
    assert error is None
    assert calls == [("GET", "/repos/fork/repo/contents/submissions/x.json?ref=abc123")]


def test_transport_failure_is_not_auto_closed(monkeypatch):
    class FakeGitHub:
        repo = "ErgoDevs/Ergo-Bounties"
        token = "secret"

        def request(self, method, path):
            raise RuntimeError("API unavailable")

    monkeypatch.setattr(triage, "urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(TimeoutError("timeout")))
    data, error = read_submission(FakeGitHub(), "submissions/x.json", "abc123", "https://raw.example/x")
    result = {"labels": [], "issues": [f"submissions/x.json: {error}"]}

    assert data is None
    assert error.startswith("cannot download submission:")
    assert should_close_invalid(result) is False
