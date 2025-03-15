"""
Module for generating language-specific markdown files.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any

from ..utils import ensure_directory, create_claim_url, format_navigation_badges, calculate_erg_value
from ..conversion_rates import convert_to_erg

# Configure logging
logger = logging.getLogger('language_generator')

def generate_language_files(
    bounty_data: List[Dict[str, Any]], 
    languages: Dict[str, List[Dict[str, Any]]],
    conversion_rates: Dict[str, float], 
    total_bounties: int, 
    currencies_count: int, 
    orgs_count: int, 
    bounties_dir: str
) -> None:
    """
    Generate language-specific markdown files.
    
    Args:
        bounty_data: List of bounty data
        languages: Dictionary of languages and their bounties
        conversion_rates: Dictionary of conversion rates
        total_bounties: Total number of bounties
        currencies_count: Number of currencies
        orgs_count: Number of organizations
        bounties_dir: Bounties directory
    """
    logger.info(f"Generating language-specific files for {len(languages)} languages")
    
    # Get currencies_dict and orgs from the processor
    from ..processor import BountyProcessor
    processor = BountyProcessor.get_instance()
    currencies_dict = processor.group_by_currency()
    orgs = processor.group_by_organization()
    
    # Create a directory for language-specific files if it doesn't exist
    lang_dir = f'{bounties_dir}/by_language'
    ensure_directory(lang_dir)
    
    # Write language-specific Markdown files
    for lang, lang_bounties in languages.items():
        # Skip any language if all its bounties have "Not specified" amounts
        if all(bounty["amount"] == "Not specified" for bounty in lang_bounties):
            logger.info(f"Skipping {lang} language as all bounties have 'Not specified' amounts")
            continue
            
        lang_file = f'{lang_dir}/{lang.lower()}.md'
        logger.debug(f"Writing language file: {lang_file}")
        
        with open(lang_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"# {lang} Bounties\n\n")
            f.write(f"*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC*\n\n")
            f.write(f"Total {lang} bounties: **{len(lang_bounties)}**\n\n")
            
            # Add navigation badges
            f.write("## Navigation\n\n")
            f.write(format_navigation_badges(
                total_bounties, 
                len(languages), 
                currencies_count, 
                orgs_count, 
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
            
            f.write("|Organisation|Repository|Title & Link|ERG Value|Paid In|Secondary Language|Reserve|\n")
            f.write("|---|---|---|---|---|---|---|\n")
            
            # Calculate ERG equivalent for each bounty for sorting
            for bounty in lang_bounties:
                amount = bounty["amount"]
                currency = bounty["currency"]
                try:
                    # Calculate ERG value for sorting
                    erg_value = calculate_erg_value(amount, currency, conversion_rates)
                    bounty["erg_value"] = erg_value
                except (ValueError, TypeError):
                    bounty["erg_value"] = 0.0
            
            # Sort bounties by ERG value (highest first)
            lang_bounties.sort(key=lambda x: x.get("erg_value", 0.0), reverse=True)
            
            # Add rows for each bounty (excluding those with "Not specified" amounts)
            has_written_row = False
            for bounty in lang_bounties:
                owner = bounty["owner"]
                title = bounty["title"]
                url = bounty["url"]
                amount = bounty["amount"]
                currency = bounty["currency"]
                secondary_lang = bounty["secondary_lang"]
                
                # Skip bounties with "Not specified" amounts, but keep at least one row for the language
                if amount == "Not specified" and has_written_row:
                    continue
                
                # Try to convert to ERG equivalent
                erg_equiv = convert_to_erg(amount, currency, conversion_rates)
                
                # Create a claim link that opens a PR template
                issue_number = bounty["issue_number"]
                creator = bounty["creator"]
                repo_name = bounty["repo"]
                
                claim_url = create_claim_url(owner, repo_name, issue_number, title, url, currency, amount, creator)
                
                # Format the currency name for the file link
                currency_file_name = currency.lower()
                if currency == "g GOLD":
                    currency_file_name = "gold"
                elif currency == "Not specified":
                    currency_file_name = "not_specified"
                
                # Add links to organization
                org_link = f"[{owner}](../by_org/{owner.lower()}.md)"
                
                # Create a nicer reserve button
                reserve_button = f"[<kbd>Reserve</kbd>]({claim_url})"
                
                f.write(f"| {org_link} | [{repo_name}](https://github.com/{owner}/{repo_name}) | [{title}]({url}) | {erg_equiv} ERG | [{currency}](../by_currency/{currency_file_name}.md) | {secondary_lang} | {reserve_button} |\n")
                has_written_row = True
    
    logger.info(f"Generated {len(languages)} language-specific files")
