#!/usr/bin/env python3
"""
Markdown Templates and Utilities Module

This module provides templates and utility functions for generating markdown content:
- Table generators for different bounty views
- Navigation and filter section generators
- Header and footer templates
- Guardrail wrappers for protecting generated content

These utilities ensure consistent formatting across all generated markdown files.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse

from .common import (
    format_navigation_badges,
    add_footer_buttons,
    get_currency_filename, # Use renamed function
    format_currency_link,
    format_organization_link,
    format_language_link,
    get_current_timestamp,
    wrap_with_guardrails,
    create_claim_url,
    get_repo_name_from_input, # Added import for helper
    escape_markdown_cell,
    escape_markdown_link_text,
)

# Configure logging
logger = logging.getLogger(__name__)


def _is_github_url(value: str) -> bool:
    parsed = urlparse(str(value))
    return parsed.scheme == "https" and parsed.netloc.lower() == "github.com"


def _safe_markdown_link(text: Any, url: Any) -> str:
    escaped = escape_markdown_link_text(text)
    url_text = str(url or "")
    return f"[{escaped}]({url_text})" if _is_github_url(url_text) else escaped

def generate_navigation_section(
    total_bounties: int, 
    languages_count: int, 
    currencies_count: int, 
    orgs_count: int, 
    conversion_rates_count: int, 
    relative_path: str = ""
) -> str:
    """
    Generate a navigation section with badges for markdown files.
    
    Args:
        total_bounties: Total number of bounties
        languages_count: Number of languages
        currencies_count: Number of currencies
        orgs_count: Number of organizations
        conversion_rates_count: Number of conversion rates
        relative_path: Relative path for links
        
    Returns:
        Formatted navigation section as markdown
    """
    content = "## Navigation\n\n"
    content += format_navigation_badges(
        total_bounties, 
        languages_count, 
        currencies_count, 
        orgs_count, 
        conversion_rates_count, 
        relative_path
    )
    content += "\n\n"
    return content

def generate_filter_section(
    languages: Dict[str, List[Dict[str, Any]]], 
    currencies_dict: Dict[str, List[Dict[str, Any]]], 
    orgs: Dict[str, List[Dict[str, Any]]],
    path_prefix: str = ""
) -> str:
    """
    Generate a filter section for markdown files.
    
    Args:
        languages: Dictionary of languages and their bounties
        currencies_dict: Dictionary of currencies and their bounties
        orgs: Dictionary of organizations and their bounties
        path_prefix: Prefix for paths in links
        
    Returns:
        Formatted filter section as markdown
    """
    content = "## Filter Bounties\n\n"
    
    # Programming Languages
    content += "**By Programming Language:** "
    lang_links = []
    for lang_name, lang_bounties_list in languages.items():
        lang_links.append(f"[{lang_name} ({len(lang_bounties_list)})]({path_prefix}by_language/{lang_name.lower()}.md)")
    content += " • ".join(lang_links)
    content += "\n\n"
    
    # Currencies
    content += "**By Currency:** "
    currency_links = []
    for currency_name, currency_bounties_list in currencies_dict.items():
        currency_file_name = get_currency_filename(currency_name)
        currency_links.append(f"[{currency_name} ({len(currency_bounties_list)})]({path_prefix}by_currency/{currency_file_name}.md)")
    content += " • ".join(currency_links)
    content += "\n\n"
    
    # Organizations
    content += "**By Organization:** "
    org_links = []
    for org_name, org_bounties_list in orgs.items():
        org_links.append(f"[{org_name} ({len(org_bounties_list)})]({path_prefix}by_org/{org_name.lower()}.md)")
    content += " • ".join(org_links)
    content += "\n\n"
    
    return content

def generate_standard_bounty_table(
    bounties: List[Dict[str, Any]],
    conversion_rates: Dict[str, float],
    show_org: bool = True,
    show_language: bool = True,
    sort_by: str = "value",
    link_prefix: str = "",
) -> str:
    """
    Generate a standard bounty table for markdown files with configurable columns.

    Args:
        bounties: List of bounty data
        conversion_rates: Dictionary of conversion rates
        show_org: Whether to include the Organisation column.
        show_language: Whether to include the Primary Language column.

    Returns:
        Formatted bounty table as markdown
    """
    from ..api.currency_client import CurrencyClient

    # Dynamically build header and separator
    header_parts = []
    separator_parts = []
    if show_org:
        header_parts.append("Organisation")
        separator_parts.append("---")
    header_parts.extend(["Bounty", "Value", "Age", "Updated", "Comments"])
    separator_parts.extend(["---", "---", "---", "---", "---"])
    if show_language:
        header_parts.append("Primary Language")
        separator_parts.append("---")
    header_parts.append("Reserve") # Reserve is always shown
    separator_parts.append("---")

    content = "|" + "|".join(header_parts) + "|\n"
    content += "|" + "|".join(separator_parts) + "|\n"

    # Set up currency client for conversions
    currency_client = CurrencyClient()
    currency_client.rates = conversion_rates

    def parse_github_date(value: str):
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    def format_age(value: str) -> str:
        parsed = parse_github_date(value)
        if not parsed:
            return "-"
        days = max((datetime.now(timezone.utc) - parsed).days, 0)
        return "today" if days == 0 else f"{days}d"

    def sort_key(bounty: Dict[str, Any]):
        if sort_by == "new":
            return parse_github_date(bounty.get("created_at", "")) or datetime.min.replace(tzinfo=timezone.utc)
        if sort_by == "updated":
            return parse_github_date(bounty.get("updated_at", "")) or datetime.min.replace(tzinfo=timezone.utc)
        if sort_by == "old":
            return parse_github_date(bounty.get("created_at", "")) or datetime.max.replace(tzinfo=timezone.utc)
        return currency_client.calculate_erg_value(bounty["amount"], bounty["currency"])

    sorted_bounties = sorted(bounties, key=sort_key, reverse=(sort_by != "old"))

    # Add rows for each bounty
    for bounty in sorted_bounties:
        owner = bounty["owner"]
        repo_name = bounty["repo"]
        title = bounty["title"]
        url = bounty["url"]
        amount = bounty["amount"]
        currency = bounty["currency"] # Needed for claim URL
        primary_lang = bounty["primary_lang"]
        issue_number = bounty["issue_number"]
        creator = bounty["creator"] # Keep creator for claim URL

        erg_value = currency_client.calculate_erg_value(amount, currency)
        if amount in {"Not specified", "Ongoing"} or erg_value <= 0.0:
            value_display = str(amount)
        elif currency == "ERG":
            value_display = f"Σ{int(erg_value)}"
        else:
            value_display = f"{amount} {currency} (~Σ{int(erg_value)})"

        # Create a claim link that opens a PR template
        claim_url = create_claim_url(owner, repo_name, issue_number, title, url, currency, amount, creator)

        # Use helper to get clean repo name and create repo link
        repo_name_simple = get_repo_name_from_input(repo_name)
        repo_url = f"https://github.com/{owner}/{repo_name_simple}"
        # Combine repo link and title link for the 'Bounty' column
        bounty_display = (
            f"{_safe_markdown_link(repo_name_simple, repo_url)}/"
            f"{_safe_markdown_link(title, url)}"
        )

        # Add organization and language links (only if shown)
        org_link = format_organization_link(owner, prefix=link_prefix) if show_org else ""
        primary_lang_link = format_language_link(primary_lang, prefix=link_prefix) if show_language else ""

        # Create a nicer reserve button/status badge using shields.io
        if "status" in bounty and bounty["status"] == "Reserved":
            # Grey badge for Reserved
            reserve_button = f"![Reserved](https://img.shields.io/badge/-Reserved-lightgrey?style=flat-square)"
        elif "status" in bounty and bounty["status"] == "In Progress":
             # Orange badge for In Progress
            reserve_button = f"![In Progress](https://img.shields.io/badge/-In%20Progress-orange?style=flat-square)"
        elif amount == "Ongoing": # Handle ongoing programs specifically
             # Link to details for ongoing programs
             reserve_button = "[Details](/docs/ongoing-programs.md)"
        else:
            # Green reserve badge/button
            reserve_button = f"[![Reserve](https://img.shields.io/badge/-Reserve-brightgreen?style=flat-square)]({claim_url})"

        age_display = format_age(bounty.get("created_at", ""))
        updated_display = format_age(bounty.get("updated_at", ""))
        comments = bounty.get("comments", 0)

        # Build row dynamically
        row_parts = []
        if show_org:
            row_parts.append(org_link)
        row_parts.extend([
            bounty_display,
            escape_markdown_cell(value_display),
            age_display,
            updated_display,
            str(comments),
        ])
        if show_language:
            row_parts.append(primary_lang_link)
        row_parts.append(reserve_button)

        content += f"| {' | '.join(row_parts)} |\n"
    return content

def generate_ongoing_programs_table(ongoing_programs: List[Dict[str, Any]], link_prefix: str = "") -> str:
    """
    Generate a table for ongoing programs.
    
    Args:
        ongoing_programs: List of ongoing program bounty data
        
    Returns:
        Formatted ongoing programs table as markdown
    """
    content = "| Organization | Program | Details | Primary Language |\n"
    content += "|-------------|---------|---------|------------------|\n"
    
    # Sort by organization
    ongoing_programs = sorted(ongoing_programs, key=lambda b: b["owner"])
    
    # Add rows for each program
    for program in ongoing_programs:
        owner = program["owner"]
        title = program["title"]
        url = program["url"]
        primary_lang = program["primary_lang"]
        
        # Add organization and language links
        org_link = format_organization_link(owner, prefix=link_prefix)
        primary_lang_link = format_language_link(primary_lang, prefix=link_prefix)
        
        content += (
            f"| {org_link} | [{escape_markdown_link_text(title)}]({url}) | "
            f"[Details]({url}) | {primary_lang_link} |\n"
        )
    
    return content

def update_readme_badges(
    total_bounties: int,
    total_value: float,
    high_value_count: int,
    languages: Dict[str, List[Dict[str, Any]]]
) -> bool:
    """
    Update the badges in the README.md file.
    
    Args:
        total_bounties: Total number of bounties
        total_value: Total ERG value of all bounties
        high_value_count: Number of high-value bounties
        languages: Dictionary of languages and their bounties
        
    Returns:
        True if successful, False otherwise
    """
    try:
        readme_path = "README.md"

        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # --- Helper for language badge update ---
        def _update_language_badge_line(line: str, langs_data: Dict[str, List[Dict[str, Any]]]) -> str:
            if "/data/by_language/" in line and "img.shields.io" in line:
                match = re.search(r'/data/by_language/(\w+)\.md.*img\.shields\.io/badge/([^-%]+)-\d+-([0-9A-F]+)', line)
                if match:
                    lang_name_in_url, badge_text, badge_color = match.groups()
                    lang_key = next((k for k in langs_data if k.lower() == lang_name_in_url), None)
                    if lang_key:
                        count = len(langs_data[lang_key])
                        new_badge_part = f'{badge_text}-{count}-{badge_color}'
                        updated_line = re.sub(r'badge/([^-%]+)-\d+-[0-9A-F]+', f'badge/{new_badge_part}', line)
                        logger.debug(f"Updated language badge line for {lang_key}: {updated_line}")
                        return updated_line
                    else:
                        logger.debug(f"No matching language key found for URL language '{lang_name_in_url}' in line: {line}")
                else:
                    logger.debug(f"Language badge line format not matched: {line}")
            return line # Return original line if no match or update needed

        # --- Define replacement rules ---
        rules = [
            # 1. General path replacement
            lambda line: line.replace("/bounties/", "/data/"),
            # 2. Specific badge value updates
            (r'Open%20Bounties-\d+(?:\+|%2B)?-4CAF50', f'Open%20Bounties-{total_bounties}%2B-4CAF50'),
            (r'Total%20Value-[\d,\.]+%20ERG-2196F3', f'Total%20Value-{total_value:,.2f}%20ERG-2196F3'),
            (r'High%20Value-\d+(?:\+|%2B)?%20Over%201000%20ERG-FFC107', f'High%20Value-{high_value_count}%2B%20Over%201000%20ERG-FFC107'),
            # 3. Language badge update (using helper)
            lambda line: _update_language_badge_line(line, languages),
            # 4. Timestamp update
            lambda line: f"<!-- Latest Update: {datetime.now(timezone.utc).strftime('%Y-%m-%d')} -->" if "Latest Update:" in line else line,
        ]

        # --- Apply rules line by line ---
        new_lines = []
        for line in content.splitlines():
            processed_line = line
            for rule in rules:
                if callable(rule):
                    processed_line = rule(processed_line)
                else:
                    pattern, replacement = rule
                    # Apply regex only if the pattern might be relevant (simple check)
                    if isinstance(pattern, str) and pattern.split('%')[0] in processed_line:
                         processed_line = re.sub(pattern, replacement, processed_line)

            if processed_line != line:
                logger.debug(f"Updated README line: {processed_line}")


            new_lines.append(processed_line)

        # Write the modified content back, ensuring a single trailing newline
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines).rstrip() + '\n')
            
        logger.info("Updated README.md badges successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error updating README.md badges: {e}")
        return False

def update_partially_generated_file(
    file_path: str,
    start_marker: str,
    end_marker: str,
    new_content: str
) -> bool:
    """
    Update a section of a file between two markers.
    
    Args:
        file_path: Path to the file to update
        start_marker: Start marker text
        end_marker: End marker text
        new_content: New content to insert between markers
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find the content between the markers
        pattern = f"({re.escape(start_marker)})(.*?)({re.escape(end_marker)})"
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            # Replace the content between the markers
            updated_content = content.replace(
                match.group(0),
                f"{start_marker}\n\n{new_content}\n\n{end_marker}"
            )
            
            # Write the updated content back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
                
            logger.info(f"Updated section in {file_path} successfully")
            return True
        else:
            logger.error(f"Could not find markers in {file_path}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating {file_path}: {e}")
        return False

# Removed wrap_with_full_guardrails as it was redundant (just called wrap_with_guardrails)
