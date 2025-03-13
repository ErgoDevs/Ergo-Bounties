"""
Module for generating language-specific markdown files.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any

from ..utils import ensure_directory, create_claim_url, format_navigation_badges
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
    
    # Create a directory for language-specific files if it doesn't exist
    lang_dir = f'{bounties_dir}/by_language'
    ensure_directory(lang_dir)
    
    # Write language-specific Markdown files
    for lang, lang_bounties in languages.items():
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
            
            f.write("|Owner|Title & Link|Bounty Amount|Paid in|Secondary Language|Claim|\n")
            f.write("|---|---|---|---|---|---|\n")
            
            # Sort bounties by owner
            lang_bounties.sort(key=lambda x: (x["owner"], x["title"]))
            
            # Add rows for each bounty
            for bounty in lang_bounties:
                owner = bounty["owner"]
                title = bounty["title"]
                url = bounty["url"]
                amount = bounty["amount"]
                currency = bounty["currency"]
                secondary_lang = bounty["secondary_lang"]
                
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
                
                f.write(f"| {owner} | [{title}]({url}) | {erg_equiv} | [{currency}](../by_currency/{currency_file_name}.md) | {secondary_lang} | [Claim]({claim_url}) |\n")
    
    logger.info(f"Generated {len(languages)} language-specific files")
