"""
Module for generating currency-specific markdown files.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any

from ..utils import ensure_directory, create_claim_url, format_navigation_badges, calculate_erg_value
from ..conversion_rates import convert_to_erg

# Configure logging
logger = logging.getLogger('currency_generator')

def load_constants() -> Dict[str, Any]:
    """
    Load constants from constants.json file.
    
    Returns:
        Dictionary of constants
        
    Raises:
        Exception: If constants.json file can't be loaded
    """
    constants_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'constants.json')
    try:
        with open(constants_path, 'r', encoding='utf-8') as f:
            constants = json.load(f)
            logger.info(f"Loaded constants from {constants_path}")
            return constants
    except Exception as e:
        logger.error(f"Error loading constants from {constants_path}: {e}")
        raise

def generate_currency_files(
    bounty_data: List[Dict[str, Any]], 
    currencies_dict: Dict[str, List[Dict[str, Any]]], 
    conversion_rates: Dict[str, float], 
    total_bounties: int, 
    languages: Dict[str, List[Dict[str, Any]]], 
    orgs: Dict[str, List[Dict[str, Any]]], 
    bounties_dir: str
) -> None:
    """
    Generate currency-specific markdown files.
    
    Args:
        bounty_data: List of bounty data
        currencies_dict: Dictionary of currencies and their bounties
        conversion_rates: Dictionary of conversion rates
        total_bounties: Total number of bounties
        languages: Dictionary of languages and their bounties
        orgs: Dictionary of organizations and their bounties
        bounties_dir: Bounties directory
    """
    logger.info(f"Generating currency-specific files for {len(currencies_dict)} currencies")
    
    # Create a directory for currency-specific files if it doesn't exist
    currency_dir = f'{bounties_dir}/by_currency'
    ensure_directory(currency_dir)
    
    # Load constants
    constants = load_constants()
    currency_file_names = constants.get("currency_file_names", {})
    
    # Write currency-specific Markdown files
    for currency, currency_bounties in currencies_dict.items():
        # Skip "Not specified" currency
        if currency == "Not specified":
            logger.info("Skipping 'Not specified' currency")
            continue
        # Format the currency name for the file using constants
        if currency in currency_file_names:
            currency_file_name = currency_file_names[currency]
        else:
            currency_file_name = currency.lower()
        
        currency_file = f'{currency_dir}/{currency_file_name}.md'
        logger.debug(f"Writing currency file: {currency_file}")
        
        with open(currency_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"# {currency} Bounties\n\n")
            f.write(f"*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC*\n\n")
            f.write(f"Total {currency} bounties: **{len(currency_bounties)}**\n\n")
            
            # Add navigation badges
            f.write("## Navigation\n\n")
            f.write(format_navigation_badges(
                total_bounties, 
                len(languages), 
                len(currencies_dict), 
                len(orgs), 
                len(conversion_rates), 
                "../"
            ))
            f.write("\n\n")
            
            # Create a unified filter section
            f.write("## Filter Bounties\n\n")
            
            # Programming Languages
            f.write("**By Programming Language:** ")
            lang_links = []
            for lang_name, lang_bounties_list in languages.items():
                lang_links.append(f"[{lang_name} ({len(lang_bounties_list)})](../by_language/{lang_name.lower()}.md)")
            f.write(" • ".join(lang_links))
            f.write("\n\n")
            
            # Currencies
            f.write("**By Currency:** ")
            currency_links = []
            for currency_name, currency_bounties_list in currencies_dict.items():
                # Format the currency name for the file link
                if currency_name == "Not specified":
                    currency_file_name = "not_specified"
                elif currency_name == "g GOLD":
                    currency_file_name = "gold"
                else:
                    currency_file_name = currency_name.lower()
                currency_links.append(f"[{currency_name} ({len(currency_bounties_list)})](../by_currency/{currency_file_name}.md)")
            f.write(" • ".join(currency_links))
            f.write("\n\n")
            
            # Organizations
            f.write("**By Organization:** ")
            org_links = []
            for org_name, org_bounties_list in orgs.items():
                org_links.append(f"[{org_name} ({len(org_bounties_list)})](../by_org/{org_name.lower()}.md)")
            f.write(" • ".join(org_links))
            f.write("\n\n")
            
            # Add conversion rate if available
            if currency in conversion_rates:
                f.write(f"## Current {currency} Rate\n\n")
                
                # Get list of currencies that don't need rate inversion
                no_rate_inversion = constants.get("no_rate_inversion", ["gGOLD"])
                
                # Invert the rate to show ERG per token (except for currencies in no_rate_inversion)
                display_rate = conversion_rates[currency]
                if currency not in no_rate_inversion:
                    display_rate = 1.0 / display_rate if display_rate > 0 else 0.0
                
                f.write(f"1 {currency} = {display_rate:.6f} ERG\n\n")
            
            f.write("|Organisation|Repository|Title & Link|Bounty Amount|ERG Equivalent|Primary Language|Reserve|\n")
            f.write("|---|---|---|---|---|---|---|\n")
            
            # Calculate ERG equivalent for each bounty for sorting
            for bounty in currency_bounties:
                amount = bounty["amount"]
                try:
                    # Calculate ERG value for sorting
                    erg_value = calculate_erg_value(amount, currency, conversion_rates)
                    bounty["erg_value"] = erg_value
                except (ValueError, TypeError):
                    bounty["erg_value"] = 0.0
            
            # Sort bounties by ERG value (highest first)
            currency_bounties.sort(key=lambda x: x.get("erg_value", 0.0), reverse=True)
            
            # Add rows for each bounty (excluding those with "Not specified" amounts)
            for bounty in currency_bounties:
                owner = bounty["owner"]
                title = bounty["title"]
                url = bounty["url"]
                amount = bounty["amount"]
                primary_lang = bounty["primary_lang"]
                
                # Skip bounties with "Not specified" amounts
                if amount == "Not specified":
                    continue
                
                # Try to convert to ERG equivalent
                erg_equiv = convert_to_erg(amount, currency, conversion_rates)
                
                # Create a claim link that opens a PR template
                issue_number = bounty["issue_number"]
                creator = bounty["creator"]
                repo_name = bounty["repo"]
                
                claim_url = create_claim_url(owner, repo_name, issue_number, title, url, currency, amount, creator)
                
                # Add organization and language links
                org_link = f"[{owner}](../by_org/{owner.lower()}.md)"
                primary_lang_link = f"[{primary_lang}](../by_language/{primary_lang.lower()}.md)"
                
                # Create a nicer reserve button
                reserve_button = f"[<kbd>Reserve</kbd>]({claim_url})"
                
                f.write(f"| {org_link} | [{repo_name}](https://github.com/{owner}/{repo_name}) | [{title}]({url}) | {amount} {currency} | {erg_equiv} ERG | {primary_lang_link} | {reserve_button} |\n")
    
    logger.info(f"Generated {len(currencies_dict)} currency-specific files")

def generate_price_table(
    conversion_rates: Dict[str, float], 
    total_bounties: int, 
    languages: Dict[str, List[Dict[str, Any]]], 
    currencies_dict: Dict[str, List[Dict[str, Any]]], 
    orgs: Dict[str, List[Dict[str, Any]]], 
    bounties_dir: str
) -> None:
    """
    Generate a currency price table markdown file.
    
    Args:
        conversion_rates: Dictionary of conversion rates
        total_bounties: Total number of bounties
        languages: Dictionary of languages and their bounties
        currencies_dict: Dictionary of currencies and their bounties
        orgs: Dictionary of organizations and their bounties
        bounties_dir: Bounties directory
    """
    logger.info("Generating currency price table")
    
    price_table_file = f'{bounties_dir}/currency_prices.md'
    with open(price_table_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write("# Currency Prices\n\n")
        f.write(f"*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC*\n\n")
        
        # Add navigation badges
        f.write("## Navigation\n\n")
        f.write(format_navigation_badges(
            total_bounties, 
            len(languages), 
            len(currencies_dict), 
            len(orgs), 
            len(conversion_rates)
        ))
        f.write("\n\n")
        
        # Create a unified filter section
        f.write("## Filter Bounties\n\n")
        
        # Programming Languages
        f.write("**By Programming Language:** ")
        lang_links = []
        for lang_name, lang_bounties_list in languages.items():
            lang_links.append(f"[{lang_name} ({len(lang_bounties_list)})](by_language/{lang_name.lower()}.md)")
        f.write(" • ".join(lang_links))
        f.write("\n\n")
        
        # Currencies
        f.write("**By Currency:** ")
        currency_links = []
        for currency_name, currency_bounties_list in currencies_dict.items():
            # Format the currency name for the file link
            if currency_name == "Not specified":
                currency_file_name = "not_specified"
            elif currency_name == "g GOLD":
                currency_file_name = "gold"
            else:
                currency_file_name = currency_name.lower()
            currency_links.append(f"[{currency_name} ({len(currency_bounties_list)})](by_currency/{currency_file_name}.md)")
        f.write(" • ".join(currency_links))
        f.write("\n\n")
        
        # Organizations
        f.write("**By Organization:** ")
        org_links = []
        for org_name, org_bounties_list in orgs.items():
            org_links.append(f"[{org_name} ({len(org_bounties_list)})](by_org/{org_name.lower()}.md)")
        f.write(" • ".join(org_links))
        f.write("\n\n")
        
        # Write price table
        f.write("## Current Prices\n\n")
        f.write("| Currency | ERG Equivalent | Notes |\n")
        f.write("|----------|----------------|-------|\n")
        
        # Load constants
        constants = load_constants()
        currency_notes = constants.get("currency_notes", {})
        currency_display_names = constants.get("currency_display_names", {})
        currency_file_names = constants.get("currency_file_names", {})
        
        # Add rows for each currency with known conversion rates
        for currency, rate in sorted(conversion_rates.items()):
            # Get notes from constants
            notes = currency_notes.get(currency, "")
            
            # Format the currency name for display using constants
            display_currency = currency_display_names.get(currency, currency)
            
            # Format the currency name for the file link using constants
            if display_currency in currency_file_names:
                file_currency = currency_file_names[display_currency]
            else:
                file_currency = display_currency.lower()
            
            currency_link = f"[{display_currency}](by_currency/{file_currency.lower()}.md)"
            
            # Get list of currencies that don't need rate inversion
            no_rate_inversion = constants.get("no_rate_inversion", ["gGOLD"])
            
            # Invert the rate to show ERG per token (except for currencies in no_rate_inversion)
            display_rate = rate
            if currency not in no_rate_inversion:
                display_rate = 1.0 / rate if rate > 0 else 0.0
            
            f.write(f"| {currency_link} | {display_rate:.6f} | {notes} |\n")
        
        f.write("\n*Note: These prices are used to calculate ERG equivalents for bounties paid in different currencies.*\n")
    
    logger.info("Generated currency price table")
