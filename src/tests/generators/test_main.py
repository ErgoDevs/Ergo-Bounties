"""
Unit tests for the main generator functions.
"""

import pytest
from unittest.mock import patch, mock_open, MagicMock
import os

# Assuming generator functions are importable like this
# Adjust the import path if necessary based on your project structure
from src.generators.main import (
    generate_language_files,
    generate_organization_files,
    generate_currency_files,
    generate_price_table,
    generate_main_file,
    generate_summary_file,
    generate_featured_bounties_file,
    update_readme_badges,
    update_ongoing_programs_table,
    generate_high_value_bounties_file,
    # Import moved functions for testing
    group_by_language,
    group_by_organization,
    group_by_currency,
    calculate_currency_totals,
    find_featured_bounties,
    find_high_value_bounties,
    find_beginner_friendly_bounties
)
from src.utils.markdown import generate_standard_bounty_table, update_readme_badges

# --- Mock Data ---

@pytest.fixture
def mock_bounty_data():
    """Provides sample bounty data."""
    return [
        {
            "timestamp": "2025-03-26 10:00:00", "owner": "org1", "repo": "repo1",
            "title": "Test Bounty 1", "url": "http://example.com/1", "amount": "100",
            "currency": "SigUSD", "primary_lang": "Python", "secondary_lang": "None",
            "labels": ["bounty", "easy"], "issue_number": 1, "creator": "user1", "status": "open",
            "value": 100.0 # Assuming pre-calculated value for simplicity in generator tests
        },
        {
            "timestamp": "2025-03-26 11:00:00", "owner": "org2", "repo": "repo2",
            "title": "Test Bounty 2", "url": "http://example.com/2", "amount": "50",
            "currency": "ERG", "primary_lang": "Rust", "secondary_lang": "None",
            "labels": ["bounty"], "issue_number": 2, "creator": "user2", "status": "open",
            "value": 50.0
        },
        {
            "timestamp": "2025-03-26 12:00:00", "owner": "org1", "repo": "repo3",
            "title": "Ongoing Program", "url": "http://example.com/3", "amount": "Ongoing",
            "currency": "Not specified", "primary_lang": "Python", "secondary_lang": "None",
            "labels": ["rewards"], "issue_number": 3, "creator": "user3", "status": "open",
            "value": 0.0
        }
    ]

@pytest.fixture
def mock_conversion_rates():
    """Provides sample conversion rates."""
    return {"SigUSD": 1.0, "ERG": 1.0, "gGOLD": 50.0}

@pytest.fixture
def mock_languages(mock_bounty_data):
    """Provides sample grouped languages."""
    # Simplified grouping for testing generators
    langs = {}
    for b in mock_bounty_data:
        lang = b['primary_lang']
        if lang not in langs: langs[lang] = []
        langs[lang].append(b)
    return langs

@pytest.fixture
def mock_orgs(mock_bounty_data):
    """Provides sample grouped orgs."""
    orgs_data = {}
    for b in mock_bounty_data:
        org = b['owner']
        if org not in orgs_data: orgs_data[org] = []
        orgs_data[org].append(b)
    return orgs_data

@pytest.fixture
def mock_currencies(mock_bounty_data):
    """Provides sample grouped currencies."""
    currencies_data = {}
    for b in mock_bounty_data:
        curr = b['currency']
        if curr == "Not specified": continue
        if curr not in currencies_data: currencies_data[curr] = []
        currencies_data[curr].append(b)
    return currencies_data


# --- Tests for Moved Functions ---

def test_group_by_language(mock_bounty_data):
    """Test the group_by_language function."""
    result = group_by_language(mock_bounty_data)
    assert "Python" in result
    assert "Rust" in result
    assert len(result["Python"]) == 2 # Includes ongoing
    assert len(result["Rust"]) == 1

def test_group_by_organization(mock_bounty_data):
    """Test the group_by_organization function."""
    result = group_by_organization(mock_bounty_data)
    assert "org1" in result
    assert "org2" in result
    assert len(result["org1"]) == 2
    assert len(result["org2"]) == 1


def test_group_by_organization_merges_case_variants():
    result = group_by_organization([
        {"owner": "StabilityNexus"},
        {"owner": "stabilitynexus"},
    ])

    assert list(result) == ["StabilityNexus"]
    assert len(result["StabilityNexus"]) == 2

def test_group_by_currency(mock_bounty_data):
    """Test the group_by_currency function."""
    result = group_by_currency(mock_bounty_data)
    assert "SigUSD" in result
    assert "ERG" in result
    assert "Not specified" not in result # Should be skipped
    assert len(result["SigUSD"]) == 1
    assert len(result["ERG"]) == 1

def test_calculate_currency_totals(mock_bounty_data, mock_conversion_rates):
    """Test the calculate_currency_totals function."""
    result = calculate_currency_totals(mock_bounty_data, mock_conversion_rates)
    assert "SigUSD" in result
    assert "ERG" in result
    assert result["SigUSD"]["count"] == 1
    assert result["SigUSD"]["value"] == 100.0 # 100 * 1.0
    assert result["ERG"]["count"] == 1
    assert result["ERG"]["value"] == 50.0 # 50 * 1.0

def test_find_featured_bounties(mock_bounty_data, mock_conversion_rates):
    """Test the find_featured_bounties function."""
    result = find_featured_bounties(mock_bounty_data, mock_conversion_rates, count=1)
    assert len(result) == 1
    assert result[0]["title"] == "Test Bounty 1" # Highest value (100 SigUSD = 100 ERG)

def test_find_high_value_bounties(mock_bounty_data, mock_conversion_rates):
    """Test the find_high_value_bounties function."""
    # Test with high threshold
    result_high = find_high_value_bounties(mock_bounty_data, mock_conversion_rates, threshold=200.0)
    assert len(result_high) == 0
    # Test with lower threshold
    result_low = find_high_value_bounties(mock_bounty_data, mock_conversion_rates, threshold=75.0)
    assert len(result_low) == 1
    assert result_low[0]["title"] == "Test Bounty 1"

def test_find_beginner_friendly_bounties(mock_bounty_data):
    """Test the find_beginner_friendly_bounties function."""
    result = find_beginner_friendly_bounties(mock_bounty_data)
    assert len(result) == 1
    assert result[0]["title"] == "Test Bounty 1" # Has "easy" label


# --- Tests for Generator Functions ---

# We use mock_open to simulate file writing without touching the disk
@patch("builtins.open", new_callable=mock_open)
@patch("src.generators.main.ensure_directory")
@patch("src.utils.common.get_current_timestamp", return_value="2025-03-26 14:00:00")
def test_generate_main_file(mock_ts, mock_ensure_dir, mock_file_open, mock_bounty_data, mock_conversion_rates):
    """Test the generate_main_file function."""
    # Removed unused args: project_totals, mock_languages, mock_currencies, mock_orgs, total_value
    total_bounties = 3
    bounties_dir = "temp_bounties"

    generate_main_file(
        mock_bounty_data,
        mock_conversion_rates,
        total_bounties,
        bounties_dir
    )

    # Check if ensure_directory was called (implicitly by grouping functions now)
    # mock_ensure_dir.assert_called() # Removed: This assertion is no longer valid for generate_main_file

    # Check if open was called correctly
    expected_file_path = os.path.join(bounties_dir, 'all.md')
    mock_file_open.assert_called_once_with(expected_file_path, 'w', encoding='utf-8')

    # Check if some expected content is in the written data
    handle = mock_file_open()
    written_content = handle.write.call_args[0][0]
    assert "# All Open Bounties" in written_content
    assert "Test Bounty 1" in written_content
    assert "Test Bounty 2" in written_content
    assert "Ongoing Program" in written_content # Check if ongoing programs are included
    assert "![All Bounties]" in written_content # Check navigation badge alt text
    assert "<!-- Generated on: 2025-03-26 14:00:00 -->" in written_content # Check timestamp format in comment

def test_bounty_table_escapes_dynamic_markdown(mock_conversion_rates):
    """Issue titles are untrusted and must not break markdown tables."""
    bounties = [{
        "owner": "org",
        "repo": "repo",
        "title": "Fix parser | handle [brackets]",
        "url": "https://github.com/org/repo/issues/1",
        "amount": "10",
        "currency": "ERG",
        "primary_lang": "Python",
        "issue_number": 1,
        "creator": "author",
        "status": "open",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
        "comments": 3,
    }]

    table = generate_standard_bounty_table(bounties, mock_conversion_rates)

    assert "Fix parser \\| handle \\[brackets\\]" in table
    assert "| 3 |" in table


def test_bounty_table_uses_link_prefix_for_subpages(mock_conversion_rates):
    bounties = [{
        "owner": "org",
        "repo": "repo",
        "title": "Fix links",
        "url": "https://github.com/org/repo/issues/1",
        "amount": "10",
        "currency": "ERG",
        "primary_lang": "Python",
        "issue_number": 1,
        "creator": "author",
        "status": "open",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
        "comments": 0,
    }]

    table = generate_standard_bounty_table(bounties, mock_conversion_rates, link_prefix="../")

    assert "[org](../by_org/org.md)" in table
    assert "[Python](../by_language/python.md)" in table


def test_bounty_table_does_not_link_non_github_bounty_url(mock_conversion_rates):
    bounties = [{
        "owner": "org",
        "repo": "repo",
        "title": "External bounty",
        "url": "javascript:alert(1)",
        "amount": "10",
        "currency": "ERG",
        "primary_lang": "Python",
        "issue_number": 1,
        "creator": "author",
        "status": "open",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
        "comments": 0,
    }]

    table = generate_standard_bounty_table(bounties, mock_conversion_rates)

    assert "[External bounty](javascript:alert(1))" not in table
    assert "External bounty" in table


def test_update_readme_badges_updates_encoded_plus_counts(tmp_path, monkeypatch):
    readme = tmp_path / "README.md"
    readme.write_text(
        "\n".join([
            "https://img.shields.io/badge/Open%20Bounties-106%2B-4CAF50",
            "https://img.shields.io/badge/💰%20Total%20Value-51,119.53%20ERG-2196F3",
            "https://img.shields.io/badge/🌟%20High%20Value-11%2B%20Over%201000%20ERG-FFC107",
            "<!-- Latest Update: 2025-10-21 -->",
        ]),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    assert update_readme_badges(108, 111126.69, 38, {}) is True

    content = readme.read_text(encoding="utf-8")
    assert "Open%20Bounties-108%2B-4CAF50" in content
    assert "Total%20Value-111,126.69%20ERG-2196F3" in content
    assert "High%20Value-38%2B%20Over%201000%20ERG-FFC107" in content
