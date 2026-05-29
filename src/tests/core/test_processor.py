"""
Unit tests for the BountyProcessor class.
"""

import pytest
import json
from unittest.mock import MagicMock, patch

# Assuming BountyProcessor is importable like this
# Adjust the import path if necessary based on your project structure
from src.core.processor import BountyProcessor
from src.api.github_client import GitHubClient
from src.api.currency_client import CurrencyClient


# Example fixture for BountyProcessor instance
@pytest.fixture
def mock_rates():
    """Provides mock currency rates."""
    return {"SigUSD": 1.0, "ERG": 1.0, "gGOLD": 50.0}

@pytest.fixture
def mock_github_client(mocker):
    """Provides a mocked GitHubClient."""
    client = mocker.MagicMock(spec=GitHubClient)
    client.get_repository_languages.return_value = ["Python", "JavaScript"]
    client.get_repository_issues.return_value = [] # Default to no issues
    client.get_organization_repos.return_value = [] # Default to no org repos
    return client

@pytest.fixture
def mock_currency_client(mocker, mock_rates):
    """Provides a mocked CurrencyClient."""
    client = mocker.MagicMock(spec=CurrencyClient)
    client.rates = mock_rates
    client.calculate_erg_value.side_effect = lambda amount, currency: float(amount) * mock_rates.get(currency, 0) if amount not in ["Not specified", "Ongoing"] else 0.0
    return client

@pytest.fixture
def processor(mock_github_client, mock_currency_client, mock_rates):
    """Provides a BountyProcessor instance with mocked dependencies."""
    # We patch the clients within the scope of the fixture/test
    with patch('src.core.processor.GitHubClient', return_value=mock_github_client), \
         patch('src.core.processor.CurrencyClient', return_value=mock_currency_client):
        # The token doesn't matter here as the client is mocked
        proc = BountyProcessor(github_token="mock_token", rates=mock_rates)
        # Ensure the mocked clients are attached if needed by tests
        proc.github_client = mock_github_client
        proc.currency_client = mock_currency_client
        return proc

# --- Test Cases ---

def test_processor_initialization(processor, mock_rates):
    """Test that the processor initializes correctly."""
    assert processor is not None
    assert processor.bounty_data == []
    assert processor.project_totals == {}
    assert processor.currency_client.rates == mock_rates
    assert processor.github_client is not None

def test_process_issue_marks_reserved_based_on_submission(processor, mock_github_client, mocker):
    """Test that an issue is marked as Reserved if a submission file exists."""
    repo_owner = "test-owner"
    repo_name = "test-repo"
    issue_number_reserved = 123
    issue_number_open = 456

    processor.reserved_bounty_ids = {f"{repo_owner}/{repo_name}#{issue_number_reserved}"}

    # Mock GitHub API to return two issues: one matching the submission, one not
    mock_issues = [
        {
            "number": issue_number_reserved,
            "title": "Bounty: Reserved Issue",
            "state": "open", # Initially open
            "labels": [{"name": "bounty"}],
            "html_url": f"https://github.com/{repo_owner}/{repo_name}/issues/{issue_number_reserved}",
            "body": "Amount: 100 ERG",
            "user": {"login": "creator1"}
        },
        {
            "number": issue_number_open,
            "title": "Bounty: Open Issue",
            "state": "open",
            "labels": [{"name": "bounty"}],
            "html_url": f"https://github.com/{repo_owner}/{repo_name}/issues/{issue_number_open}",
            "body": "Amount: 50 ERG",
            "user": {"login": "creator2"}
        }
    ]
    mock_github_client.get_repository_issues.return_value = mock_issues

    # Define the repository to process
    repos_to_query = [{"owner": repo_owner, "repo": repo_name}]

    # Run the processing
    processor.process_repositories(repos_to_query)

    # Assertions
    assert processor.reserved_count == 1, "Should have counted one reserved bounty"
    assert len(processor.bounty_data) == 2, "Should have processed both issues"

    reserved_bounty = next((b for b in processor.bounty_data if b["issue_number"] == issue_number_reserved), None)
    open_bounty = next((b for b in processor.bounty_data if b["issue_number"] == issue_number_open), None)

    assert reserved_bounty is not None, "Reserved bounty should be in the data"
    assert reserved_bounty["status"] == "Reserved", "Status should be updated to Reserved"
    assert reserved_bounty["amount"] == "100", "Amount should be extracted correctly"
    assert reserved_bounty["currency"] == "ERG", "Currency should be extracted correctly"

    assert open_bounty is not None, "Open bounty should be in the data"
    assert open_bounty["status"] == "open", "Status should remain open"
    assert open_bounty["amount"] == "50", "Amount should be extracted correctly"
    assert open_bounty["currency"] == "ERG", "Currency should be extracted correctly"


def test_process_issue_reservation_uses_full_bounty_id(processor):
    """Same issue number in another repo must not be marked reserved."""
    processor.reserved_bounty_ids = {"test-owner/test-repo#123"}
    issue = {
        "number": 123,
        "title": "Bounty: Other repo issue",
        "state": "open",
        "labels": [{"name": "bounty"}],
        "html_url": "https://github.com/test-owner/other-repo/issues/123",
        "body": "Amount: 50 ERG",
        "user": {"login": "creator"},
    }
    processor.project_totals["test-owner"] = {"count": 0, "value": 0.0}

    processor._process_issue(issue, "test-owner", "other-repo", "Python", "None")

    assert processor.bounty_data[0]["status"] == "open"
    assert processor.reserved_count == 0


def test_reserved_bounty_ids_ignore_placeholders_and_use_bounty_id(tmp_path, monkeypatch, mock_github_client, mock_currency_client, mock_rates):
    """Only active, non-placeholder submissions should reserve exact bounty IDs."""
    submissions = tmp_path / "submissions"
    submissions.mkdir()
    (submissions / "valid.json").write_text(json.dumps({
        "status": "in-progress",
        "contributor": "alice",
        "wallet_address": "9abc",
        "bounty_id": "Owner/Repo#12",
    }), encoding="utf-8")
    (submissions / "placeholder.json").write_text(json.dumps({
        "status": "in-progress",
        "contributor": "bob",
        "wallet_address": "YOUR_WALLET_ADDRESS",
        "bounty_id": "Owner/Other#12",
    }), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    with patch('src.core.processor.GitHubClient', return_value=mock_github_client), \
         patch('src.core.processor.CurrencyClient', return_value=mock_currency_client):
        proc = BountyProcessor(github_token="mock_token", rates=mock_rates)

    assert proc.reserved_bounty_ids == {"owner/repo#12"}


def test_process_organizations_dedupes_case_insensitive(processor, mock_github_client):
    processor.github_client = mock_github_client
    mock_github_client.get_organization_repos.return_value = [
        {"name": "BenefactionPlatform-Ergo", "archived": False, "fork": False, "has_issues": True}
    ]

    repos = processor.process_organizations(
        [{"org": "stabilitynexus"}],
        [{"owner": "StabilityNexus", "repo": "BenefactionPlatform-Ergo"}],
    )

    assert repos == [{"owner": "StabilityNexus", "repo": "BenefactionPlatform-Ergo"}]


def test_project_totals_merge_owner_case(processor):
    processor.project_totals["stabilitynexus"] = {"count": 1, "value": 0.0}

    processor.add_extra_bounties([{
        "owner": "StabilityNexus",
        "repo": "BenefactionPlatform-Ergo",
        "amount": "100",
        "currency": "ERG",
    }])

    assert list(processor.project_totals) == ["stabilitynexus"]
    assert processor.project_totals["stabilitynexus"]["count"] == 2
    assert processor.project_totals["stabilitynexus"]["value"] == 100.0
