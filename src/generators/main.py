#!/usr/bin/env python3
"""
Output Generators Module

This module contains functions for generating various markdown output files:
- Language-specific files
- Organization-specific files
- Currency-specific files
- Summary files
- Featured bounties
- High-value bounties
- Price tables

Each generator function follows a similar pattern: it takes input data, processes it,
formats markdown content, and writes output files.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any
from pathlib import Path
import os
import json # Added json import for CONSTANTS loading

# Import from sibling modules and parent packages
from ..utils.common import (
    ensure_directory,
    get_current_timestamp,
    create_claim_url,
    get_currency_filename,
    get_currency_display_name,
    escape_markdown_link_text,
    # CONSTANTS # Load constants locally in this module instead
)
from ..utils.markdown import (
    generate_navigation_section,
    # generate_filter_section, # Not used currently
    generate_standard_bounty_table,
    generate_ongoing_programs_table,
    update_readme_badges,
    update_partially_generated_file,
    wrap_with_guardrails,
    add_footer_buttons,
    # format_currency_filename, # Removed, use get_currency_filename
    format_currency_link,
    format_organization_link,
    format_language_link
)
from ..api.currency_client import CurrencyClient

# Configure logging
logger = logging.getLogger(__name__)

# --- Load Constants Locally ---
CONSTANTS_PATH = Path(__file__).parent.parent / 'config' / 'constants.json'
CONSTANTS = {}
try:
    with open(CONSTANTS_PATH, 'r', encoding='utf-8') as f:
        CONSTANTS = json.load(f)
    logger.info(f"Loaded constants for generators from {CONSTANTS_PATH}")
except Exception as e:
    logger.warning(f"Could not load constants from {CONSTANTS_PATH} for generators: {e}")
# --- End Load Constants ---


# --- Grouping and Filtering Functions (Moved from BountyProcessor) ---

def group_by_language(bounty_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group bounties by language.

    Args:
        bounty_data: List of bounty data dictionaries

    Returns:
        Dictionary of language -> list of bounties
    """
    languages = {}
    for bounty in bounty_data:
        # Skip bounties with "Not specified" amounts for "Unknown" language
        if bounty["primary_lang"] == "Unknown" and bounty["amount"] == "Not specified":
            continue

        primary_lang = bounty["primary_lang"]
        if primary_lang not in languages:
            languages[primary_lang] = []
        languages[primary_lang].append(bounty)

    # Remove "Unknown" language if it's empty after filtering
    if "Unknown" in languages and len(languages["Unknown"]) == 0:
        del languages["Unknown"]

    return languages


def group_by_organization(bounty_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group bounties by organization.

    Args:
        bounty_data: List of bounty data dictionaries

    Returns:
        Dictionary of organization -> list of bounties
    """
    orgs = {}
    for bounty in bounty_data:
        owner = bounty["owner"]
        org_key = next((key for key in orgs if key.lower() == owner.lower()), owner)
        if org_key not in orgs:
            orgs[org_key] = []
        orgs[org_key].append(bounty)
    return orgs


def group_by_currency(bounty_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group bounties by currency.

    Args:
        bounty_data: List of bounty data dictionaries

    Returns:
        Dictionary of currency -> list of bounties
    """
    currencies_dict = {}
    for bounty in bounty_data:
        currency = bounty["currency"]

        # Skip "Not specified" currency
        if currency == "Not specified":
            continue

        if currency not in currencies_dict:
            currencies_dict[currency] = []
        currencies_dict[currency].append(bounty)
    return currencies_dict


def calculate_currency_totals(
    bounty_data: List[Dict[str, Any]],
    conversion_rates: Dict[str, float]
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate totals by currency.

    Args:
        bounty_data: List of bounty data dictionaries
        conversion_rates: Dictionary of currency conversion rates

    Returns:
        Dictionary of currency -> {count, value} totals
    """
    currency_totals = {}
    currencies_dict = group_by_currency(bounty_data)
    currency_client = CurrencyClient()
    currency_client.rates = conversion_rates

    for currency, currency_bounties in currencies_dict.items():
        # Count only bounties with specified amounts (excluding "Ongoing" programs)
        specified_bounties = [
            b for b in currency_bounties
            if b["amount"] != "Not specified" and b["amount"] != "Ongoing"
        ]

        currency_totals[currency] = {
            "count": len(specified_bounties),
            "value": 0.0
        }

        # Calculate total value
        for bounty in specified_bounties:
            amount = bounty["amount"]
            currency_totals[currency]["value"] += currency_client.calculate_erg_value(
                amount, currency
            )

    return currency_totals


def find_featured_bounties(
    bounty_data: List[Dict[str, Any]],
    conversion_rates: Dict[str, float],
    count: int = 2
) -> List[Dict[str, Any]]:
    """
    Find the highest-value bounties to feature.

    Args:
        bounty_data: List of bounty data dictionaries
        conversion_rates: Dictionary of currency conversion rates
        count: Number of featured bounties to return

    Returns:
        List of high-value bounty objects with ERG value
    """
    featured_bounties = []
    currency_client = CurrencyClient()
    currency_client.rates = conversion_rates

    for bounty in bounty_data:
        amount = bounty["amount"]
        currency = bounty["currency"]

        if amount != "Not specified" and amount != "Ongoing":
            try:
                # Calculate ERG equivalent
                value = currency_client.calculate_erg_value(amount, currency)

                featured_bounties.append({
                    **bounty,
                    "value": value
                })
            except (ValueError, TypeError):
                pass

    # Sort by value and get top bounties
    featured_bounties.sort(key=lambda x: x["value"], reverse=True)
    return featured_bounties[:count]


def find_high_value_bounties(
    bounty_data: List[Dict[str, Any]],
    conversion_rates: Dict[str, float],
    threshold: float = 1000.0
) -> List[Dict[str, Any]]:
    """
    Find bounties with value above a threshold.

    Args:
        bounty_data: List of bounty data dictionaries
        conversion_rates: Dictionary of currency conversion rates
        threshold: Minimum ERG value for high-value bounties

    Returns:
        List of high-value bounty objects sorted by value
    """
    high_value_bounties = []
    currency_client = CurrencyClient()
    currency_client.rates = conversion_rates

    for bounty in bounty_data:
        amount = bounty["amount"]
        currency = bounty["currency"]

        if amount != "Not specified" and amount != "Ongoing":
            try:
                # Calculate ERG equivalent
                value = currency_client.calculate_erg_value(amount, currency)

                if value >= threshold:
                    high_value_bounties.append({
                        **bounty,
                        "value": value,
                        "status": bounty.get("status", "")
                    })
            except (ValueError, TypeError):
                pass

    # Sort by value
    high_value_bounties.sort(key=lambda x: x["value"], reverse=True)
    return high_value_bounties


def find_beginner_friendly_bounties(bounty_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Find bounties that are tagged as beginner-friendly.

    Args:
        bounty_data: List of bounty data dictionaries

    Returns:
        List of beginner-friendly bounty objects
    """
    beginner_tags = [
        'beginner', 'beginner-friendly', 'good-first-issue',
        'good first issue', 'easy', 'starter', 'newbie'
    ]

    beginner_bounties = []

    for bounty in bounty_data:
        labels = [label.lower() for label in bounty.get("labels", [])]

        if any(tag in label for tag in beginner_tags for label in labels):
            beginner_bounties.append(bounty)

    return beginner_bounties


# --- Generator Functions ---

def _clear_markdown_dir(directory: Path) -> None:
    """Remove old generated markdown pages before writing current category pages."""
    ensure_directory(directory)
    for path in directory.glob("*.md"):
        try:
            path.unlink()
        except OSError as e:
            logger.error(f"Error removing stale generated file {path}: {e}")
            raise

def _generate_markdown_page(
    filename: str,
    title: str,
    page_bounties: List[Dict[str, Any]],
    all_bounty_data: List[Dict[str, Any]], # Needed for global counts
    conversion_rates: Dict[str, float],
    total_bounties: int, # Overall total
    nav_relative_path: str = "../",
    extra_content: str = "", # For things like currency rate display
    # Add flags to control table columns
    show_org: bool = True,
    show_language: bool = True,
    sort_by: str = "value"
) -> None:
    """
    Helper function to generate a standard markdown bounty page.

    Args:
        filename: The output markdown file path.
        title: The H1 title for the page.
        page_bounties: List of bounties specific to this page.
        all_bounty_data: Full list of all bounties (for calculating global counts).
        conversion_rates: Dictionary of conversion rates.
        total_bounties: Total number of bounties across all categories.
        nav_relative_path: Relative path for navigation links.
        extra_content: Optional extra markdown content to insert before the main table.
    """
    logger.debug(f"Generating page: {filename}")

    # Calculate necessary counts for navigation
    languages = group_by_language(all_bounty_data)
    currencies_dict = group_by_currency(all_bounty_data)
    orgs = group_by_organization(all_bounty_data)
    # Include "Not specified" if present for accurate count
    currencies_count = len(currencies_dict) + (1 if any(b["currency"] == "Not specified" for b in all_bounty_data) else 0)
    orgs_count = len(orgs)
    languages_count = len(languages)

    # Calculate total value for this specific page
    currency_client = CurrencyClient()
    currency_client.rates = conversion_rates
    page_value = sum(
        currency_client.calculate_erg_value(b["amount"], b["currency"])
        for b in page_bounties
        if b["amount"] != "Not specified" and b["amount"] != "Ongoing"
    )
    page_bounty_count = len(page_bounties)

    # Build content
    content = ""
    content += f"*Report generated: {get_current_timestamp()} UTC*\n\n"
    # Add stats badges for the specific page
    content += f"![Total Bounties: {page_bounty_count}](https://img.shields.io/badge/Total%20Bounties-{page_bounty_count}-blue)"
    if page_value > 0: # Only show value if it's positive
        content += f" ![Total Value: {page_value:.2f} ERG](https://img.shields.io/badge/Total%20Value-{page_value:.2f}%20ERG-green)"
    content += "\n\n"

    # Add navigation badges (using global counts)
    content += generate_navigation_section(
        total_bounties,
        languages_count,
        currencies_count,
        orgs_count,
        len(conversion_rates),
        nav_relative_path
    )

    # Add any extra content provided
    if extra_content:
        content += extra_content + "\n"

    # Add the main bounty table for the page, passing the flags
    content += f"## {title.lstrip('# ')}\n\n" # Use title for H2 heading
    content += generate_standard_bounty_table(
        page_bounties,
        conversion_rates,
        show_org=show_org,
        show_language=show_language,
        sort_by=sort_by,
        link_prefix=nav_relative_path
    )

    # Add footer buttons
    content += add_footer_buttons(nav_relative_path)

    # Wrap with guardrails
    final_content = wrap_with_guardrails(content, title) # Use wrap_with_guardrails

    # Write to file
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(final_content)
        logger.debug(f"Successfully wrote {filename}")
    except Exception as e:
        logger.error(f"Error writing file {filename}: {e}")


def generate_language_files(
    bounty_data: List[Dict[str, Any]],
    conversion_rates: Dict[str, float],
    total_bounties: int,
    bounties_dir: str
) -> None:
    """
    Generate language-specific markdown files.

    Args:
        bounty_data: List of bounty data
        conversion_rates: Dictionary of conversion rates
        total_bounties: Total number of bounties
        bounties_dir: Bounties directory
    """
    languages = group_by_language(bounty_data)
    language_dir = Path(bounties_dir) / 'by_language'
    _clear_markdown_dir(language_dir)

    logger.info(f"Generating language-specific files for {len(languages)} languages")

    for language, language_bounties in languages.items():
        language_file = language_dir / f'{language.lower()}.md'
        page_title = f"# {language} Bounties"

        _generate_markdown_page(
            filename=str(language_file),
            title=page_title,
            page_bounties=language_bounties,
            all_bounty_data=bounty_data,
            conversion_rates=conversion_rates,
            total_bounties=total_bounties,
            nav_relative_path="../",
            show_language=False # Don't show language column on language page
        )
    logger.info(f"Generated {len(languages)} language-specific files")


def generate_organization_files(
    bounty_data: List[Dict[str, Any]],
    conversion_rates: Dict[str, float],
    total_bounties: int,
    bounties_dir: str
) -> None:
    """
    Generate organization-specific markdown files.

    Args:
        bounty_data: List of bounty data
        conversion_rates: Dictionary of conversion rates
        total_bounties: Total number of bounties
        bounties_dir: Bounties directory
    """
    orgs = group_by_organization(bounty_data)
    org_dir = Path(bounties_dir) / 'by_org'
    _clear_markdown_dir(org_dir)

    logger.info(f"Generating organization-specific files for {len(orgs)} organizations")

    for org, org_bounties in orgs.items():
        org_file = org_dir / f'{org.lower()}.md'
        page_title = f"# {org} Bounties"

        _generate_markdown_page(
            filename=str(org_file),
            title=page_title,
            page_bounties=org_bounties,
            all_bounty_data=bounty_data,
            conversion_rates=conversion_rates,
            total_bounties=total_bounties,
            nav_relative_path="../",
            show_org=False # Don't show org column on org page
        )
    logger.info(f"Generated {len(orgs)} organization-specific files")


def generate_currency_files(
    bounty_data: List[Dict[str, Any]],
    conversion_rates: Dict[str, float],
    total_bounties: int,
    bounties_dir: str
) -> None:
    """
    Generate currency-specific markdown files.

    Args:
        bounty_data: List of bounty data
        conversion_rates: Dictionary of conversion rates
        total_bounties: Total number of bounties
        bounties_dir: Bounties directory
    """
    currencies_dict = group_by_currency(bounty_data)
    currency_dir = Path(bounties_dir) / 'by_currency'
    _clear_markdown_dir(currency_dir)

    logger.info(f"Generating currency-specific files for {len(currencies_dict)} currencies")

    # Reverted: Write currency-specific Markdown files manually
    languages = group_by_language(bounty_data) # Needed for nav
    orgs = group_by_organization(bounty_data) # Needed for nav
    currencies_count = len(currencies_dict) + (1 if any(b["currency"] == "Not specified" for b in bounty_data) else 0) # Needed for nav

    currency_client = CurrencyClient() # Needed for value calc
    currency_client.rates = conversion_rates

    for currency, currency_bounties in currencies_dict.items():
        currency_file_name = get_currency_filename(currency)
        currency_file = currency_dir / f'{currency_file_name}.md'
        display_name = get_currency_display_name(currency)
        page_title = f"# {display_name} Bounties"

        currency_value = sum(
            currency_client.calculate_erg_value(b["amount"], currency)
            for b in currency_bounties
            if b["amount"] != "Not specified" and b["amount"] != "Ongoing"
        )

        content = ""
        content += f"*Report generated: {get_current_timestamp()} UTC*\n\n"
        content += f"![Total Bounties: {len(currency_bounties)}](https://img.shields.io/badge/Total%20Bounties-{len(currency_bounties)}-blue) "
        if currency_value > 0:
             content += f"![Total Value: {currency_value:.2f} ERG](https://img.shields.io/badge/Total%20Value-{currency_value:.2f}%20ERG-green)"
        content += "\n\n"

        content += generate_navigation_section(
            total_bounties,
            len(languages),
            currencies_count,
            len(orgs),
            len(conversion_rates),
            "../"
        )

        if currency in conversion_rates:
            rate = conversion_rates[currency]
            no_rate_inversion = CONSTANTS.get("no_rate_inversion", [])
            display_rate = 1.0 / rate if currency not in no_rate_inversion and rate > 0 else rate
            content += f"## Current {display_name} Rate\n\n1 {currency} = {display_rate:.6f} ERG\n\n"

        content += f"## {display_name} Bounties\n\n"
        # Currency pages show all columns (defaults are True)
        content += generate_standard_bounty_table(currency_bounties, conversion_rates, link_prefix="../")
        content += add_footer_buttons("../")

        final_content = wrap_with_guardrails(content, page_title)
        try:
            with open(currency_file, 'w', encoding='utf-8') as f:
                f.write(final_content)
            logger.debug(f"Successfully wrote {currency_file}")
        except Exception as e:
            logger.error(f"Error writing file {currency_file}: {e}")


    # Don't forget the "Not specified" currency
    not_specified_bounties = [
        b for b in bounty_data if b["currency"] == "Not specified"
    ]

    if not_specified_bounties:
        not_specified_file = currency_dir / 'not_specified.md'
        page_title = "# Bounties with Unspecified Value"

        # Build content manually for this special case
        content = ""
        content += f"*Report generated: {get_current_timestamp()} UTC*\n\n"
        content += f"![Total Bounties: {len(not_specified_bounties)}](https://img.shields.io/badge/Total%20Bounties-{len(not_specified_bounties)}-blue)\n\n"
        content += generate_navigation_section(
            total_bounties,
            len(languages), # Recalculate or pass if needed
            currencies_count,
            len(orgs), # Recalculate or pass if needed
            len(conversion_rates),
            "../"
        )
        content += "## Bounties with Unspecified Value\n\n"
        # Not specified page shows all columns (defaults are True)
        content += generate_standard_bounty_table(not_specified_bounties, conversion_rates, link_prefix="../")
        content += "\n[View summary of bounties with unspecified value in summary file →](../summary.md#bounties-with-unspecified-value)\n\n"
        content += add_footer_buttons("../")

        final_content = wrap_with_guardrails(content, page_title)
        try:
            # Cast Path to string for open()
            with open(str(not_specified_file), 'w', encoding='utf-8') as f:
                f.write(final_content)
            logger.debug(f"Successfully wrote {not_specified_file}")
        except Exception as e:
             logger.error(f"Error writing file {not_specified_file}: {e}")


    logger.info(f"Generated {len(currencies_dict) + (1 if not_specified_bounties else 0)} currency-specific files")


def generate_price_table(
    bounty_data: List[Dict[str, Any]], # Added bounty_data
    conversion_rates: Dict[str, float],
    total_bounties: int,
    bounties_dir: str
) -> None:
    """
    Generate a currency price table markdown file.

    Args:
        bounty_data: List of bounty data
        conversion_rates: Dictionary of conversion rates
        total_bounties: Total number of bounties
        bounties_dir: Bounties directory
    """
    languages = group_by_language(bounty_data)
    currencies_dict = group_by_currency(bounty_data)
    orgs = group_by_organization(bounty_data)
    currencies_count = len(currencies_dict) + (1 if any(b["currency"] == "Not specified" for b in bounty_data) else 0)

    logger.info("Generating currency price table")

    price_table_file = Path(bounties_dir) / 'currency_prices.md' # Use Path

    # Build content
    content = ""

    # Add timestamp - no need to add title here as it's added by wrap_with_guardrails
    content += f"*Report generated: {get_current_timestamp()} UTC*\n\n"

    # Add navigation badges
    content += generate_navigation_section(
        total_bounties,
        len(languages),
        currencies_count, # Use calculated count
        len(orgs),
        len(conversion_rates)
    )


    # Currency notes mapping from constants
    currency_notes = CONSTANTS.get("currency_notes", {})

    # Write price table
    content += "## Current Prices\n\n"
    content += "| Currency | ERG Equivalent | Notes |\n"
    content += "|----------|----------------|-------|\n"

    # Add rows for each currency with known conversion rates
    for currency, rate in sorted(conversion_rates.items()):
        # Get notes
        notes = currency_notes.get(currency, "")

        # Create currency link using display name
        currency_link = format_currency_link(currency)

        # Get list of currencies that don't need rate inversion from constants
        no_rate_inversion = CONSTANTS.get("no_rate_inversion", [])

        # Invert the rate to show ERG per token (except for currencies in no_rate_inversion)
        display_rate = rate
        if currency not in no_rate_inversion:
            display_rate = 1.0 / rate if rate > 0 else 0.0

        content += f"| {currency_link} | {display_rate:.6f} | {notes} |\n"

    content += "\n*Note: These prices are used to calculate ERG equivalents for bounties paid in different currencies.*\n"

    # Add section explaining how prices are retrieved
    content += "\n## How Prices are Retrieved\n\n"
    content += "The currency prices are retrieved using different APIs:\n\n"

    # SigUSD, GORT, RSN
    content += "### Spectrum API\n\n"
    content += "SigUSD, GORT, and RSN prices are retrieved from the [Spectrum.fi](https://spectrum.fi/) API:\n\n"
    content += "```\n"
    content += "GET https://api.spectrum.fi/v1/price-tracking/markets\n"
    content += "```\n\n"
    content += "The API returns market data for various trading pairs. We filter this data to find specific currency pairs:\n\n"
    content += "- For SigUSD: We look for markets where `quoteSymbol=SigUSD` and `baseSymbol=ERG`\n"
    content += "- For GORT: We look for markets where `quoteSymbol=GORT` and `baseSymbol=ERG`\n"
    content += "- For RSN: We look for markets where `quoteSymbol=RSN` and `baseSymbol=ERG`\n\n"

    # BENE
    content += "### BENE\n\n"
    content += "BENE price is set to be equivalent to SigUSD (which is pegged to USD), making 1 BENE equal to $1 worth of ERG.\n\n"

    # g GOLD
    content += "### Gold Price from Oracle Pool\n\n"
    content += "The price of gold (g GOLD) is retrieved from the XAU/ERG oracle pool using the Ergo Explorer API:\n\n"
    content += "```\n"
    content += "GET https://api.ergoplatform.com/api/v1/boxes/unspent/byTokenId/3c45f29a5165b030fdb5eaf5d81f8108f9d8f507b31487dd51f4ae08fe07cf4a\n"
    content += "```\n\n"
    content += "This queries for unspent boxes containing the oracle pool NFT. The price is extracted from the R4 register of the latest box.\n\n"

    # Add footer with action buttons
    content += add_footer_buttons()

    # Wrap with guardrails
    final_content = wrap_with_guardrails(content, "# Currency Prices") # Use wrap_with_guardrails

    # Write to file
    # Cast Path to string for open()
    with open(str(price_table_file), 'w', encoding='utf-8') as f:
        f.write(final_content)

    logger.info("Generated currency price table")


def generate_high_value_bounties_file(
    bounty_data: List[Dict[str, Any]],
    conversion_rates: Dict[str, float],
    total_bounties: int,
    bounties_dir: str,
    high_value_threshold: float = 1000.0
) -> None:
    """
    Generate a high-value bounties markdown file. (Reverted - Not using helper)

    Args:
        bounty_data: List of bounty data
        conversion_rates: Dictionary of conversion rates
        total_bounties: Total number of bounties
        bounties_dir: Bounties directory
        high_value_threshold: Minimum ERG value to be considered high-value
    """
    languages = group_by_language(bounty_data)
    currencies_dict = group_by_currency(bounty_data)
    orgs = group_by_organization(bounty_data)
    currencies_count = len(currencies_dict) + (1 if any(b["currency"] == "Not specified" for b in bounty_data) else 0)

    logger.info(f"Generating high-value bounties file (threshold: {high_value_threshold} ERG)")

    # Find high-value bounties using the module-level function
    high_value_bounties = find_high_value_bounties(bounty_data, conversion_rates, threshold=high_value_threshold)

    high_value_file = Path(bounties_dir) / 'high-value-bounties.md' # Use Path
    page_title = f"# High-Value Bounties (Over {high_value_threshold:,.0f} ERG)"

    # Build content manually
    content = ""
    content += f"*Report generated: {get_current_timestamp()} UTC*\n\n"
    content += f"Total high-value bounties: **{len(high_value_bounties)}**\n\n"
    content += generate_navigation_section(
        total_bounties,
        len(languages),
        currencies_count,
        len(orgs),
        len(conversion_rates),
        "" # Relative path from data/
    )
    content += f"## {page_title.lstrip('# ')}\n\n" # Use title for H2
    # Custom table for high-value bounties
    content += "| Bounty | Organization | Value | Currency | Primary Language | Reserve |\n"
    content += "|--------|--------------|-------|----------|------------------|--------|\n"
    for bounty in high_value_bounties:
        owner = bounty["owner"]
        repo_name = bounty["repo"]
        title = bounty["title"]
        url = bounty["url"]
        currency = bounty["currency"]
        primary_lang = bounty["primary_lang"]
        issue_number = bounty["issue_number"]
        creator = bounty["creator"]
        amount = bounty["amount"]
        erg_value = bounty["value"]
        claim_url = create_claim_url(owner, repo_name, issue_number, title, url, currency, amount, creator)
        org_link = format_organization_link(owner)
        primary_lang_link = format_language_link(primary_lang)
        currency_link = format_currency_link(currency)
        reserve_button = "Reserved" if bounty.get("status") == "In Progress" else f"[<kbd>Reserve</kbd>]({claim_url})"
        content += f"| [{title}]({url}) | {org_link} | {erg_value:.2f} ERG | {currency_link} | {primary_lang_link} | {reserve_button} |\n"

    content += add_footer_buttons()

    final_content = wrap_with_guardrails(content, page_title)
    try:
        # Cast Path to string for open()
        with open(str(high_value_file), 'w', encoding='utf-8') as f:
            f.write(final_content)
        logger.info(f"Generated high-value bounties file with {len(high_value_bounties)} bounties")
    except Exception as e:
        logger.error(f"Error writing file {high_value_file}: {e}")


def generate_main_file(
    bounty_data: List[Dict[str, Any]],
    conversion_rates: Dict[str, float],
    total_bounties: int,
    bounties_dir: str
) -> None:
    """
    Generate the main markdown file with all bounties. (Reverted - Not using helper)

    Args:
        bounty_data: List of bounty data
        conversion_rates: Dictionary of conversion rates
        total_bounties: Total number of bounties
        bounties_dir: Bounties directory
    """
    languages = group_by_language(bounty_data)
    currencies_dict = group_by_currency(bounty_data)
    orgs = group_by_organization(bounty_data)
    currencies_count = len(currencies_dict) + (1 if any(b["currency"] == "Not specified" for b in bounty_data) else 0)

    logger.info("Generating main bounty file")

    md_file = Path(bounties_dir) / 'all.md' # Use Path
    page_title = "# All Open Bounties"

    # Build content manually
    content = ""
    content += f"*Report generated: {get_current_timestamp()} UTC*\n\n"
    content += generate_navigation_section(
        total_bounties,
        len(languages),
        currencies_count,
        len(orgs),
        len(conversion_rates),
        "" # Relative path from data/
    )

    ongoing_programs = [b for b in bounty_data if b["amount"] == "Ongoing"]
    if ongoing_programs:
        content += "## Ongoing Reward Programs\n\n"
        content += "The Ergo ecosystem offers ongoing reward programs to encourage continuous contributions in key areas.\n\n"
        content += "**[View Ongoing Programs →](/docs/ongoing-programs.md)**\n\n"

    content += "## All Bounties\n\n"
    # Main page shows all columns (defaults are True)
    content += generate_standard_bounty_table(bounty_data, conversion_rates)
    content += add_footer_buttons()

    final_content = wrap_with_guardrails(content, page_title)
    try:
        # Cast Path to string for open()
        with open(str(md_file), 'w', encoding='utf-8') as f:
            f.write(final_content)
        logger.info("Generated main bounty file")
    except Exception as e:
        logger.error(f"Error writing file {md_file}: {e}")


def generate_bounty_discovery_files(
    bounty_data: List[Dict[str, Any]],
    conversion_rates: Dict[str, float],
    total_bounties: int,
    bounties_dir: str
) -> None:
    """Generate alternate bounty views for discovery and maintenance."""
    now = datetime.now(timezone.utc)

    def parse_dt(value: str):
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    def age_days(bounty: Dict[str, Any]) -> int:
        created = parse_dt(bounty.get("created_at", ""))
        return (now - created).days if created else 0

    beginner = find_beginner_friendly_bounties(bounty_data)
    stale = [b for b in bounty_data if age_days(b) >= 180 and b.get("status", "").lower() == "open"]

    views = [
        ("new-bounties.md", "# New Bounties", bounty_data, "new"),
        ("recently-active.md", "# Recently Active Bounties", bounty_data, "updated"),
        ("stale-bounties.md", "# Stale Bounties", stale, "old"),
        ("starter-bounties.md", "# Starter Bounties", beginner, "updated"),
    ]

    for filename, title, bounties, sort_by in views:
        _generate_markdown_page(
            filename=str(Path(bounties_dir) / filename),
            title=title,
            page_bounties=bounties,
            all_bounty_data=bounty_data,
            conversion_rates=conversion_rates,
            total_bounties=total_bounties,
            nav_relative_path="",
            sort_by=sort_by
        )


def generate_summary_file(
    bounty_data: List[Dict[str, Any]], # Added bounty_data
    project_totals: Dict[str, Dict[str, Any]],
    conversion_rates: Dict[str, float],
    total_bounties: int,
    total_value: float,
    bounties_dir: str
) -> None:
    """
    Generate a summary markdown file for README reference.

    Args:
        bounty_data: List of bounty data
        project_totals: Dictionary of project totals
        conversion_rates: Dictionary of conversion rates
        total_bounties: Total number of bounties
        total_value: Total value of bounties
        bounties_dir: Bounties directory
    """
    languages = group_by_language(bounty_data)
    currencies_dict = group_by_currency(bounty_data)
    orgs = group_by_organization(bounty_data)
    currencies_count = len(currencies_dict) + (1 if any(b["currency"] == "Not specified" for b in bounty_data) else 0)

    logger.info("Generating summary file")

    summary_file = f'{bounties_dir}/summary.md'

    # Build content
    #content = "## 📋 Open Bounties\n\n"
    #content += f"**[View Current Open Bounties →](/{bounties_dir}/all.md)**\n\n"

    # Add navigation badges with links to respective headers
    content = generate_navigation_section(
        total_bounties,
        len(languages),
        currencies_count, # Use calculated count
        len(orgs),
        len(conversion_rates),
        f"/{bounties_dir}/" # Correct relative path for summary in root data dir
    )

    # Projects section
    content += "## Projects\n\n"
    content += "| Project | Count | Value |\n"
    content += "|----------|-------|-------|\n"

    # Add rows for major projects (those with more than 1 bounty)
    for owner, totals in sorted(project_totals.items(), key=lambda x: x[1]["value"], reverse=True):
        if totals["count"] > 0:
            # Add link to organization page
            org_link = f"[{owner}](/{bounties_dir}/by_org/{owner.lower()}.md)"
            content += f"| {org_link} | {totals['count']} | {totals['value']:,.2f} ERG |\n"

    # Add overall total
    content += f"| **Total** | **{total_bounties}** | **{total_value:,.2f} ERG** |\n\n"


    # Calculate currency totals using the module-level function
    currency_totals = calculate_currency_totals(bounty_data, conversion_rates)

    # Add currency breakdown
    content += "## Currencies\n\n"

    content += "Open bounties are updated daily with values shown in ERG equivalent. Some bounties may be paid in other tokens as noted in the \"Paid in\" column of the bounty listings.\n"

    content += f"\n[View current currency prices →](/{bounties_dir}/currency_prices.md)\n"

    content += "| Currency | Count | Total Value (ERG) |\n"
    content += "|----------|-------|------------------|\n"

    # Write currency rows (top 5 by value)
    for currency, totals in sorted(currency_totals.items(), key=lambda x: x[1]["value"], reverse=True)[:5]:
        # Format the currency name for the file link
        currency_file_name = get_currency_filename(currency) # Use renamed util function

        # Add link to currency page
        # Use display name for link text
        display_name = get_currency_display_name(currency)
        currency_link = f"[{display_name}](/{bounties_dir}/by_currency/{currency_file_name}.md)"

        content += f"| {currency_link} | {totals['count']} | {totals['value']:.2f} |\n"

    content += f"\n[View all currencies →](/{bounties_dir}/by_currency/)\n\n"

    # Add language breakdown
    content += "## Languages\n\n"
    content += "| Language | Count | Percentage |\n"
    content += "|----------|-------|------------|\n"

    # Write language rows (top 5 by count)
    for lang, lang_bounties in sorted(languages.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        count = len(lang_bounties)
        percentage = (count / total_bounties) * 100 if total_bounties > 0 else 0
        content += f"| [{lang}](/{bounties_dir}/by_language/{lang.lower()}.md) | {count} | {percentage:.1f}% |\n"

    content += f"\n[View all languages →](/{bounties_dir}/by_language/)\n\n"



    # Add footer with action buttons
    content += add_footer_buttons()

    # Wrap with guardrails
    final_content = wrap_with_guardrails(content, "# Summary of Bounties") # Use wrap_with_guardrails

    # Write to file
    # Cast Path to string for open()
    with open(str(summary_file), 'w', encoding='utf-8') as f:
        f.write(final_content)

    logger.info("Generated summary file")

    # Update README badges
    # from ..utils.markdown import update_readme_badges # Already imported
    # Calculate high value count here before passing to update_readme_badges
    high_value_bounties = find_high_value_bounties(bounty_data, conversion_rates) # Use default threshold
    update_readme_badges(total_bounties, total_value, len(high_value_bounties), languages)


def update_ongoing_programs_table(
    bounty_data: List[Dict[str, Any]],
    conversion_rates: Dict[str, float],
    bounties_dir: str # This argument seems unused here, consider removing
) -> None:
    """
    Update the tables in the ongoing programs markdown file using guardrails.

    Args:
        bounty_data: List of bounty data
        conversion_rates: Dictionary of conversion rates
        bounties_dir: Bounties directory (unused)
    """
    logger.info("Updating ongoing programs tables with guardrails")

    # Filter for ongoing programs (amount == "Ongoing")
    ongoing_programs = [b for b in bounty_data if b["amount"] == "Ongoing"]

    if ongoing_programs:
        # Generate the ongoing programs table content
        ongoing_table_content = generate_ongoing_programs_table(ongoing_programs, link_prefix="/data/")

        # Update the table between guardrails
        try:
            # Read the file
            with open('docs/ongoing-programs.md', 'r', encoding='utf-8') as f:
                content = f.read()

            # Find the ongoing programs table section
            start_marker = "<!-- BEGIN_ONGOING_PROGRAMS_TABLE -->"
            end_marker = "<!-- END_ONGOING_PROGRAMS_TABLE -->"

            start_pos = content.find(start_marker)
            end_pos = content.find(end_marker)

            if start_pos != -1 and end_pos != -1:
                # Replace the content between the markers
                pre_content = content[:start_pos + len(start_marker)]
                post_content = content[end_pos:]

                # Construct the new content
                new_content = pre_content + "\n" + ongoing_table_content + "\n" + post_content

                # Write the updated content back to the file
                with open('docs/ongoing-programs.md', 'w', encoding='utf-8') as f:
                    f.write(new_content)

                logger.info("Successfully updated ongoing programs table with guardrails")
            else:
                logger.error("Could not find ongoing programs table markers in ongoing-programs.md")
        except Exception as e:
            logger.error(f"Error updating ongoing programs table: {e}")
    else:
        logger.info("No ongoing programs found, skipping ongoing table update")

    # Filter for extra bounties from src/config/extra_bounties.json (only those with "bounty" label)
    # The assumption is that bounties from extra_bounties.json will have distinctive characteristics
    extra_bounties = []

    # import json # Already imported at top level

    # extra_bounties = [] # Already initialized

    # Load extra bounties data from JSON file
    try:
        with open("src/config/extra_bounties.json", "r", encoding="utf-8") as f:
            extra_bounties_data = json.load(f)
    except FileNotFoundError:
        logger.error("Could not find extra_bounties.json")
        extra_bounties_data = []

    # Filter for extra bounties by comparing against loaded JSON data
    for bounty in bounty_data:
        for extra_bounty in extra_bounties_data:
            if (
                bounty.get("url") == extra_bounty.get("url")
                and bounty.get("title") == extra_bounty.get("title")
            ):
                extra_bounties.append(bounty)
                break  # Move to the next bounty in bounty_data

    if extra_bounties:
        # Generate the extra bounties table with an explanatory header
        intro_text = "These grants and additional bounties are pulled from src/config/extra_bounties.json:\n\n"
        # Ongoing programs page shows all columns (defaults are True)
        bounty_table_content = intro_text + generate_standard_bounty_table(
            extra_bounties,
            conversion_rates,
            link_prefix="/data/"
        )

        # Update the table between guardrails
        try:
            # Read the file
            with open('docs/ongoing-programs.md', 'r', encoding='utf-8') as f:
                content = f.read()

            # Find the active bounties table section
            start_marker = "<!-- BEGIN_ACTIVE_BOUNTIES_TABLE -->"
            end_marker = "<!-- END_ACTIVE_BOUNTIES_TABLE -->"

            start_pos = content.find(start_marker)
            end_pos = content.find(end_marker)

            if start_pos != -1 and end_pos != -1:
                # Replace the content between the markers
                pre_content = content[:start_pos + len(start_marker)]
                post_content = content[end_pos:]

                # Construct the new content
                new_content = pre_content + "\n" + bounty_table_content + "\n" + post_content

                # Write the updated content back to the file
                with open('docs/ongoing-programs.md', 'w', encoding='utf-8') as f:
                    f.write(new_content)

                logger.info("Successfully updated grants and additional bounties table with guardrails")
            else:
                logger.error("Could not find active bounties table markers in ongoing-programs.md")
        except Exception as e:
            logger.error(f"Error updating grants and additional bounties table: {e}")
    else:
        logger.info("No extra bounties found, skipping bounties table update")

def generate_featured_bounties_file(
    bounty_data: List[Dict[str, Any]],
    conversion_rates: Dict[str, float],
    total_bounties: int,
    total_value: float,
    # languages: Dict[str, List[Dict[str, Any]]], # Removed, calculated internally
    # currencies_dict: Dict[str, List[Dict[str, Any]]], # Removed, calculated internally
    # orgs: Dict[str, List[Dict[str, Any]]], # Removed, calculated internally
    bounties_dir: str
) -> None:
    """
    Generate a featured bounties markdown file.

    Args:
        bounty_data: List of bounty data
        conversion_rates: Dictionary of conversion rates
        total_bounties: Total number of bounties
        total_value: Total value of bounties
        # languages: Dictionary of languages and their bounties # Removed
        # currencies_dict: Dictionary of currencies and their bounties # Removed
        # orgs: Dictionary of organizations and their bounties # Removed
        bounties_dir: Bounties directory
    """
    languages = group_by_language(bounty_data) # Calculate internally
    currencies_dict = group_by_currency(bounty_data) # Calculate internally
    orgs = group_by_organization(bounty_data)
    currencies_count = len(currencies_dict) + (1 if any(b["currency"] == "Not specified" for b in bounty_data) else 0)

    logger.info("Generating featured bounties file")

    # Find top bounties using the module-level function
    featured_bounties = find_featured_bounties(bounty_data, conversion_rates, count=2)

    featured_bounties_file = f'{bounties_dir}/featured_bounties.md'

    # Build content
    content = ""

    # Add navigation section
    content += generate_navigation_section(
        total_bounties,
        len(languages),
        currencies_count, # Use calculated count
        len(orgs),
        len(conversion_rates)
    )

    # Get current date for the week row
    current_date = datetime.now(timezone.utc).strftime("%b %d, %Y")

    # Write the featured bounties table
    content += "## Top Bounties by Value\n\n"
    content += "| Bounty | Organization | Value | Currency |\n"
    content += "|--------|--------------|-------|----------|\n"

    # Add rows for featured bounties
    for bounty in featured_bounties:
        # Format links
        org_link = format_organization_link(bounty['owner'])
        currency_link = format_currency_link(bounty['currency'])

        # Calculate ERG equivalent
        erg_equiv = bounty["value"]

        content += f"| [{escape_markdown_link_text(bounty['title'])}]({bounty['url']}) | {org_link} | {erg_equiv:.2f} ERG | {currency_link} |\n"

    content += "\n## Weekly Summary\n\n"
    content += "| Date | Open Bounties | Total Value |\n"
    content += "|------|--------------|-------------|\n"
    content += f"| [{current_date}](/{bounties_dir}/all.md#all-bounties) | {total_bounties} | {total_value:,.2f} ERG |\n\n"

    # Add footer with action buttons
    content += add_footer_buttons()

    # Wrap with guardrails
    final_content = wrap_with_guardrails(content, "# Featured Bounties") # Use wrap_with_guardrails

    # Write to file
    # Cast Path to string for open()
    with open(str(featured_bounties_file), 'w', encoding='utf-8') as f:
        f.write(final_content)

    logger.info("Generated featured bounties file")
