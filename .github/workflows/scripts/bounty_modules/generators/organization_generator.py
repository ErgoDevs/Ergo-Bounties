"""
Module for generating organization-specific markdown files.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any

from ..utils import ensure_directory, create_claim_url, format_navigation_badges, calculate_erg_value
from ..conversion_rates import convert_to_erg

# Configure logging
logger = logging.getLogger('organization_generator')

def generate_organization_files(
    bounty_data: List[Dict[str, Any]], 
    orgs: Dict[str, List[Dict[str, Any]]], 
    conversion_rates: Dict[str, float], 
    total_bounties: int, 
    languages: Dict[str, List[Dict[str, Any]]], 
    currencies_count: int, 
    bounties_dir: str
) -> None:
    """
    Generate organization-specific markdown files.
    
    Args:
        bounty_data: List of bounty data
        orgs: Dictionary of organizations and their bounties
        conversion_rates: Dictionary of conversion rates
        total_bounties: Total number of bounties
        languages: Dictionary of languages and their bounties
        currencies_count: Number of currencies
        bounties_dir: Bounties directory
    """
    logger.info(f"Generating organization-specific files for {len(orgs)} organizations")
    
    # Get currencies_dict from the processor
    from ..processor import BountyProcessor
    processor = BountyProcessor.get_instance()
    currencies_dict = processor.group_by_currency()
    
    # Create a directory for organization-specific files if it doesn't exist
    org_dir = f'{bounties_dir}/by_org'
    ensure_directory(org_dir)
    
    # Write organization-specific Markdown files
    for org, org_bounties in orgs.items():
        org_file = f'{org_dir}/{org.lower()}.md'
        logger.debug(f"Writing organization file: {org_file}")
        
        with open(org_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"# {org} Bounties\n\n")
            f.write(f"*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC*\n\n")
            f.write(f"Total {org} bounties: **{len(org_bounties)}**\n\n")
            
            # Add navigation badges
            f.write("## Navigation\n\n")
            f.write(format_navigation_badges(
                total_bounties, 
                len(languages), 
                currencies_count, 
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
            
            f.write("|Repository|Title & Link|ERG Value|Paid In|Primary Language|Secondary Language|Reserve|\n")
            f.write("|---|---|---|---|---|---|---|\n")
            
            # Calculate ERG equivalent for each bounty for sorting
            for bounty in org_bounties:
                amount = bounty["amount"]
                currency = bounty["currency"]
                try:
                    # Calculate ERG value for sorting
                    erg_value = calculate_erg_value(amount, currency, conversion_rates)
                    bounty["erg_value"] = erg_value
                except (ValueError, TypeError):
                    bounty["erg_value"] = 0.0
            
            # Sort bounties by ERG value (highest first)
            org_bounties.sort(key=lambda x: x.get("erg_value", 0.0), reverse=True)
            
            # Add rows for each bounty (excluding those with "Not specified" amounts)
            for bounty in org_bounties:
                title = bounty["title"]
                url = bounty["url"]
                amount = bounty["amount"]
                currency = bounty["currency"]
                primary_lang = bounty["primary_lang"]
                secondary_lang = bounty["secondary_lang"]
                
                # Skip bounties with "Not specified" amounts
                if amount == "Not specified":
                    continue
                
                # Try to convert to ERG equivalent
                erg_equiv = convert_to_erg(amount, currency, conversion_rates)
                
                # Create a claim link that opens a PR template
                issue_number = bounty["issue_number"]
                creator = bounty["creator"]
                repo_name = bounty["repo"]
                
                claim_url = create_claim_url(bounty['owner'], repo_name, issue_number, title, url, currency, amount, creator)
                
                # Add language links
                primary_lang_link = f"[{primary_lang}](../by_language/{primary_lang.lower()}.md)"
                
                # Format the currency name for the file link
                currency_file_name = currency.lower()
                if currency == "g GOLD":
                    currency_file_name = "gold"
                elif currency == "Not specified":
                    currency_file_name = "not_specified"
                
                # Create a nicer reserve button
                reserve_button = f"[<kbd>Reserve</kbd>]({claim_url})"
                
                f.write(f"| [{repo_name}](https://github.com/{bounty['owner']}/{repo_name}) | [{title}]({url}) | {erg_equiv} ERG | [{currency}](../by_currency/{currency_file_name}.md) | {primary_lang_link} | {secondary_lang} | {reserve_button} |\n")
    
    logger.info(f"Generated {len(orgs)} organization-specific files")
