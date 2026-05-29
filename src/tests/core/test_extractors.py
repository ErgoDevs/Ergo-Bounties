from src.core.extractors import extract_bounty_info, extract_from_labels, extract_from_text, is_bounty_issue


def test_detects_bounty_from_title_and_labels():
    assert is_bounty_issue("Bounty: implement parser", []) is True
    assert is_bounty_issue("Implement parser", [{"name": "b-100-erg"}]) is True
    assert is_bounty_issue("Implement parser", [{"name": "bug"}]) is False


def test_extracts_currency_amount_from_labels():
    assert extract_from_labels([{"name": "bounty-100erg"}]) == ("100", "ERG")
    assert extract_from_labels([{"name": "b-50sigusd"}]) == ("50", "SigUSD")


def test_extracts_precious_metal_amount_from_labels():
    assert extract_from_labels([{"name": "bounty-2g gold"}]) == ("2", "g GOLD")


def test_extracts_currency_amount_from_text():
    assert extract_from_text("Fix wallet", "Bounty: 1,000 SigUSD") == ("1000", "SigUSD")
    assert extract_from_text("50 ERG bounty", "") == ("50", "ERG")


def test_extracts_no_amount_fallback():
    issue = {
        "title": "Bounty without amount",
        "body": "Needs work",
        "labels": [{"name": "bounty"}],
    }

    assert extract_bounty_info(issue) == ("Not specified", "Not specified")
