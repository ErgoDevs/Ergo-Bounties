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
