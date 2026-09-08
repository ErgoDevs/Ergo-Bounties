from scripts.triage_submission_prs import bounty_claims, earlier_claims, md_text, normalize_bounty_id, select_prs_to_triage, should_close_invalid


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


def test_first_claim_on_a_bounty_is_not_a_duplicate():
    claims = {"owner/repo#12": [43, 48]}

    # the first claimant has nobody ahead of it, so it is not flagged and survives
    assert earlier_claims("owner/repo#12", 43, claims) == []
    # the later one is
    assert earlier_claims("owner/repo#12", 48, claims) == [43]


def test_competing_claims_do_not_close_each_other():
    """Both claimants used to be labelled duplicate-bounty, and should_close_invalid closes on that
    label, so two claims on one bounty closed each other and left the bounty unclaimed."""
    claims = {"owner/repo#12": [43, 48]}

    def closes(pr_number: int) -> bool:
        duplicates = earlier_claims("owner/repo#12", pr_number, claims)
        labels = ["duplicate-bounty"] if duplicates else []
        return should_close_invalid({"labels": labels, "issues": []})

    assert closes(43) is False
    assert closes(48) is True


def test_claims_on_different_bounties_never_collide():
    claims = {"owner/repo#12": [43], "owner/repo#99": [48]}

    assert earlier_claims("owner/repo#99", 48, claims) == []


def test_a_submission_without_a_bounty_id_is_never_a_duplicate():
    assert earlier_claims("", 48, {"owner/repo#12": [43]}) == []
