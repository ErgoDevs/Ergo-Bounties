#!/usr/bin/env python3
"""
Common Utilities Module

This module provides utility functions used throughout the application:
- Directory operations (creating directories)
- Date and time formatting
- String formatting and conversion
- URL generation

These utility functions are designed to be reusable components that help with
common tasks across the application.
"""

import os
import json
import logging
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Union, Optional, List

# Configure logging
logger = logging.getLogger(__name__)

# --- Load Constants for Utilities ---
CONSTANTS_PATH = Path(__file__).parent.parent / 'config' / 'constants.json'
CONSTANTS = {}
try:
    with open(CONSTANTS_PATH, 'r', encoding='utf-8') as f:
        CONSTANTS = json.load(f)
    logger.info(f"Loaded constants for utils from {CONSTANTS_PATH}")
except Exception as e:
    logger.warning(f"Could not load constants from {CONSTANTS_PATH} for utils: {e}")

CURRENCY_FILE_NAMES = CONSTANTS.get("currency_file_names", {})
CURRENCY_DISPLAY_NAMES = CONSTANTS.get("currency_display_names", {})
# --- End Load Constants ---


def get_repo_name_from_input(repo_input: str) -> str:
    """
    Extracts the repository name, handling potential full URLs.
    Removes 'http(s)://' and any trailing '/tree/...'.

    Args:
        repo_input: The repository name or full URL.

    Returns:
        The extracted repository name.
    """
    if repo_input.startswith('http://') or repo_input.startswith('https://'):
        # Remove protocol and split by '/'
        path_parts = repo_input.replace('https://', '').replace('http://', '').rstrip('/').split('/')
        # Find 'tree' index if it exists
        tree_index = -1
        try:
            tree_index = path_parts.index('tree')
        except ValueError:
            pass # 'tree' not found

        # Get the part before 'tree' or the last part
        if tree_index > 0:
            # Typically owner/repo, so index before 'tree' should be repo name
            # Ensure we don't go out of bounds if URL is malformed
             if tree_index -1 < len(path_parts):
                 return path_parts[tree_index - 1]
        elif path_parts:
             # Return last part, assuming it's the repo name in owner/repo format
             return path_parts[-1]
        # Fallback if parsing fails unexpectedly
        logger.warning(f"Could not reliably parse repo name from URL: {repo_input}")
        return repo_input # Return original input as fallback
    # If it doesn't start with http, assume it's already the name
    return repo_input

def ensure_directory(directory: Union[str, Path]) -> None:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory: Directory path to create
    """
    try:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {e}")
        raise

def create_claim_url(
    owner: str,
    repo_name: str,
    issue_number: int,
    title: str,
    url: str,
    currency: str,
    amount: str,
    creator: str
) -> str:
    """
    Create a URL for claiming a bounty through a GitHub PR.

    Args:
        owner: Repository owner
        repo_name: Repository name (can be a full URL)
        issue_number: Issue number
        title: Issue title
        url: Issue URL
        currency: Bounty currency
        amount: Bounty amount
        creator: Issue creator

    Returns:
        URL that opens a GitHub PR with pre-filled template
    """
    # Use helper to get clean repo name for filename
    repo_name_simple = get_repo_name_from_input(repo_name)

    logger.debug(f"Creating claim URL for {owner}/{repo_name_simple}#{issue_number}")

    # Create JSON template using json.dumps to properly escape special characters
    template_data = {
        "contributor": "YOUR_GITHUB_USERNAME",
        "wallet_address": "YOUR_WALLET_ADDRESS",
        "contact_method": "YOUR_CONTACT_INFO",
        "work_link": "",
        "work_title": title,
        "bounty_id": f"{owner}/{repo_name}#{issue_number}", # Keep original repo_name here for ID consistency? Or simple? Let's keep original for now.
        "original_issue_link": url,
        "payment_currency": currency,
        "bounty_value": 0 if amount in ["Not specified", "Ongoing"] else float(amount) if amount.replace('.', '', 1).isdigit() else 0,
        "status": "in-progress",
        "submission_date": "",
        "expected_completion": "YYYY-MM-DD",
        "description": "I am working on this bounty",
        "review_notes": "",
        "payment_tx_id": "",
        "payment_date": ""
    }

    # Convert to JSON and URL encode
    json_content = json.dumps(template_data, indent=2)
    encoded_json = urllib.parse.quote(json_content)

    # Create the claim URL
    claim_url = (
        f"https://github.com/ErgoDevs/Ergo-Bounties/new/main"
        f"?filename=submissions/{owner.lower()}-{repo_name_simple.lower()}-{issue_number}.json" # Use simple name for filename
        f"&value={encoded_json}"
        f"&message=Claim%20Bounty%20{owner}/{repo_name_simple}%23{issue_number}" # Use simple name in message too
        f"&description=I%20want%20to%20claim%20this%20bounty%20posted%20by%20{creator}.%0A%0ABounty:%20{urllib.parse.quote(title)}"
    )

    return claim_url

def get_current_timestamp() -> str:
    """
    Get current timestamp in a formatted string.

    Returns:
        Formatted timestamp (YYYY-MM-DD HH:MM:SS)
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def escape_markdown_cell(value: Any) -> str:
    """Escape dynamic text for a GitHub markdown table cell."""
    text = "" if value is None else str(value)
    return text.replace("\r", " ").replace("\n", " ").replace("|", "\\|")


def escape_markdown_link_text(value: Any) -> str:
    """Escape dynamic text used inside markdown link brackets."""
    text = "" if value is None else str(value)
    return (
        text.replace("\r", " ")
        .replace("\n", " ")
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )

def format_navigation_badges(
    total_bounties: int,
    languages_count: int,
    currencies_count: int,
    orgs_count: int,
    conversion_rates_count: int,
    relative_path: str = ""
) -> str:
    """
    Format navigation badges for markdown files.

    Args:
        total_bounties: Total number of bounties
        languages_count: Number of languages
        currencies_count: Number of currencies
        orgs_count: Number of organizations
        conversion_rates_count: Number of conversion rates
        relative_path: Relative path for links (e.g., "../" for subdirectories)

    Returns:
        Formatted navigation badges as markdown
    """
    badges = []
    badges.append(f"[![All Bounties](https://img.shields.io/badge/All%20Bounties-{total_bounties}-blue)]({relative_path}all.md)")
    badges.append(f"[![By Language](https://img.shields.io/badge/By%20Language-{languages_count}-green)]({relative_path}summary.md#languages)")
    badges.append(f"[![By Currency](https://img.shields.io/badge/By%20Currency-{currencies_count}-yellow)]({relative_path}summary.md#currencies)")
    badges.append(f"[![By Organization](https://img.shields.io/badge/By%20Organization-{orgs_count}-orange)]({relative_path}summary.md#projects)")
    badges.append(f"[![New](https://img.shields.io/badge/New-Recent-blueviolet)]({relative_path}new-bounties.md)")
    badges.append(f"[![Active](https://img.shields.io/badge/Recently%20Active-Updated-success)]({relative_path}recently-active.md)")
    badges.append(f"[![Starter](https://img.shields.io/badge/Starter-Friendly-brightgreen)]({relative_path}starter-bounties.md)")
    badges.append(f"[![Stale](https://img.shields.io/badge/Stale-180d%2B-lightgrey)]({relative_path}stale-bounties.md)")


    return " ".join(badges)

def add_footer_buttons(relative_path: str = "") -> str:
    """
    Add standard footer buttons to markdown files.

    Args:
        relative_path: Relative path for links (e.g., "../" for subdirectories)

    Returns:
        HTML code for footer buttons
    """
    return f"""

---

<div align="center">
  <p>
    <a href="{relative_path}../docs/donate.md"><img src="https://img.shields.io/badge/❤️%20Donate-F44336" alt="Donate"></a>
    <a href="{relative_path}../docs/bounty-submission-guide.md#reserving-a-bounty"><img src="https://img.shields.io/badge/🔒%20How%20To%20Claim-4CAF50" alt="Claim a Bounty"></a>
  </p>
</div>
"""

# Renamed from format_currency_filename and consolidated logic from config.py
def get_currency_filename(currency: str) -> str:
    """
    Get the filename to use for a currency, using constants if available.

    Args:
        currency: Currency name or code

    Returns:
        Normalized filename for the currency
    """
    # Use loaded constants map first
    if currency in CURRENCY_FILE_NAMES:
        return CURRENCY_FILE_NAMES[currency]
    # Fallback logic (same as before, but now centralized)
    elif currency == "Not specified":
        return "not_specified"
    # Handle both 'g GOLD' and 'gGOLD' consistently if needed
    elif currency == "g GOLD" or currency == "gGOLD":
        return "gold"
    else:
        # Default to lowercase if no specific rule
        return currency.lower()

# New function, logic moved from config.py
def get_currency_display_name(currency: str) -> str:
    """
    Get the display name for a currency, using constants if available.

    Args:
        currency: Currency code

    Returns:
        Formatted display name for the currency, or the original code if not found.
    """
    # Use loaded constants map
    return CURRENCY_DISPLAY_NAMES.get(currency, currency)


def format_currency_link(currency: str, directory: str = "by_currency", prefix: str = "") -> str:
    """
    Format a currency name as a link to its dedicated page.

    Args:
        currency: Currency name or code
        directory: Directory containing currency files

    Returns:
        Markdown link to the currency page
    """
    filename = get_currency_filename(currency) # Use the consolidated function
    display_name = get_currency_display_name(currency) # Use the new display name function
    return f"[{display_name}]({prefix}{directory}/{filename}.md)"

def format_organization_link(org: str, directory: str = "by_org", prefix: str = "") -> str:
    """
    Format an organization name as a link to its dedicated page.

    Args:
        org: Organization name
        directory: Directory containing organization files

    Returns:
        Markdown link to the organization page
    """
    return f"[{org}]({prefix}{directory}/{org.lower()}.md)"

def format_language_link(language: str, directory: str = "by_language", prefix: str = "") -> str:
    """
    Format a language name as a link to its dedicated page.

    Args:
        language: Programming language name
        directory: Directory containing language files

    Returns:
        Markdown link to the language page
    """
    return f"[{language}]({prefix}{directory}/{language.lower()}.md)"

def wrap_with_guardrails(content: str, header: str = "") -> str:
    """
    Wrap content with guardrails for protection against automatic updates.

    Args:
        content: Markdown content
        header: Optional header to include before the content

    Returns:
        Content wrapped with guardrails
    """
    timestamp = get_current_timestamp()

    guardrails = f"""<!-- GENERATED FILE - DO NOT EDIT DIRECTLY -->
<!-- Generated on: {timestamp} -->

{header}

{content}

<!-- END OF GENERATED CONTENT -->
"""
    return guardrails
