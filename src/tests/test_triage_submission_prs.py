from scripts.triage_submission_prs import bounty_claims, md_text, normalize_bounty_id, select_prs_to_triage, should_close_invalid


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


def test_ongoing_program_submissions_allow_zero_value_and_multiple_contributors():
    from unittest.mock import MagicMock
    from scripts.triage_submission_prs import ONGOING_PROGRAMS_DOC_URL, validate_submission

    submissions = {
        10: [{"data": {"bounty_id": "program-dev"}}],
        11: [{"data": {"bounty_id": "program-dev"}}],
    }
    claims = bounty_claims(submissions)
    assert claims == {}

    gh = MagicMock()
    gh.request.return_value = {"merged": True, "state": "closed"}
    pr = {"number": 10, "user": {"login": "alice"}}
    data = {
        "contributor": "alice",
        "wallet_address": "9fZuV28GTZbHJFkhQAi1y979PDa81fu68fqae9WTUeaTaDFLfWZ",
        "work_link": "https://github.com/ErgoDevs/Ergo-Bounties/pull/61",
        "work_title": "Flag possibly-resolved bounties",
        "bounty_id": "program-dev",
        "original_issue_link": ONGOING_PROGRAMS_DOC_URL,
        "payment_currency": "ERG",
        "bounty_value": 0,
        "status": "awaiting-review",
        "submission_date": "2026-11-21",
    }
    issues, labels, bounty_id, linked_merged, _reviewer, _exp = validate_submission(
        gh, pr, "submissions/alice-development-flag.json", data, claims
    )
    assert issues == []
    assert labels == {"ready-review"}
    assert bounty_id == "program-dev"
    assert linked_merged is True


def test_in_progress_reservation_allows_empty_submission_date():
    from unittest.mock import MagicMock
    from scripts.triage_submission_prs import validate_submission

    gh = MagicMock()
    gh.request.return_value = {"user": {"login": "kushti"}}
    pr = {"number": 12, "user": {"login": "bob"}}
    data = {
        "contributor": "bob",
        "wallet_address": "9fZuV28GTZbHJFkhQAi1y979PDa81fu68fqae9WTUeaTaDFLfWZ",
        "work_link": "",
        "work_title": "Test reservation",
        "bounty_id": "ergoplatform/ergo#1952",
        "original_issue_link": "https://github.com/ergoplatform/ergo/issues/1952",
        "payment_currency": "SigUSD",
        "bounty_value": 500,
        "status": "in-progress",
        "submission_date": "",
        "expected_completion": "2027-01-15",
    }
    issues, labels, *_ = validate_submission(
        gh, pr, "submissions/bob-ergo-1952.json", data, {}
    )
    assert issues == []
    assert "invalid-submission" not in labels
