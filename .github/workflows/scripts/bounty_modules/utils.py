import os
import json
import logging
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Union, Optional

# Configure logging
logger = logging.getLogger('utils')

def ensure_directory(directory: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path to create
    """
    try:
        os.makedirs(directory, exist_ok=True)
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
        repo_name: Repository name
        issue_number: Issue number
        title: Issue title
        url: Issue URL
        currency: Bounty currency
        amount: Bounty amount
        creator: Issue creator
        
    Returns:
        URL that opens a GitHub PR with pre-filled template
    """
    logger.debug(f"Creating claim URL for {owner}/{repo_name}#{issue_number}")
    
    # Create JSON template using json.dumps to properly escape special characters
    template_data = {
        "contributor": "YOUR_GITHUB_USERNAME",
        "wallet_address": "YOUR_WALLET_ADDRESS",
        "contact_method": "YOUR_CONTACT_INFO",
        "work_link": "",
        "work_title": title,
        "bounty_id": f"{owner}/{repo_name}#{issue_number}",
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
        f"?filename=submissions/{owner.lower()}-{repo_name.lower()}-{issue_number}.json"
        f"&value={encoded_json}"
        f"&message=Claim%20Bounty%20{owner}/{repo_name}%23{issue_number}"
        f"&description=I%20want%20to%20claim%20this%20bounty%20posted%20by%20{creator}.%0A%0ABounty:%20{urllib.parse.quote(title)}"
    )
    
    return claim_url

def get_current_timestamp() -> str:
    """
    Get current timestamp in a formatted string.
    
    Returns:
        Formatted timestamp (YYYY-MM-DD HH:MM:SS)
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate_erg_value(
    amount: str, 
    currency: str, 
    conversion_rates: Dict[str, float]
) -> float:
    """
    Calculate ERG value from amount and currency.
    
    Args:
        amount: Amount as a string
        currency: Currency code
        conversion_rates: Dictionary of conversion rates
        
    Returns:
        ERG value as a float, or 0 if conversion not possible
    
    Examples:
        - calculate_erg_value("100", "ERG", rates) -> 100.0
        - calculate_erg_value("50", "SigUSD", rates) -> ERG equivalent of 50 SigUSD
        - calculate_erg_value("2", "g GOLD", rates) -> ERG equivalent of 2g of gold
        - calculate_erg_value("Ongoing", "ERG", rates) -> 0.0 (special case for ongoing programs)
    """
    if amount == "Not specified" or amount == "Ongoing":
        return 0.0
        
    try:
        if currency == "ERG":
            return float(amount)
        elif currency == "SigUSD" and "SigUSD" in conversion_rates:
            return float(amount) / conversion_rates["SigUSD"]
        elif currency == "GORT" and "GORT" in conversion_rates:
            return float(amount) / conversion_rates["GORT"]
        elif currency == "RSN" and "RSN" in conversion_rates:
            return float(amount) / conversion_rates["RSN"]
        elif currency == "BENE" and "BENE" in conversion_rates:
            return float(amount) / conversion_rates["BENE"]  # BENE is worth $1 in ERG
        elif currency == "g GOLD" and "gGOLD" in conversion_rates:
            return float(amount) * conversion_rates["gGOLD"]
        else:
            logger.warning(f"Unknown currency or missing conversion rate: {currency}")
            return 0.0
    except ValueError as e:
        logger.error(f"Error converting {amount} {currency} to ERG: {e}")
        return 0.0

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
    badges.append(f"[![All Bounties](https://img.shields.io/badge/All_Bounties-{total_bounties}-blue)]({relative_path}all.md)")
    badges.append(f"[![By Language](https://img.shields.io/badge/By_Language-{languages_count}-green)]({relative_path}by_language/)")
    badges.append(f"[![By Currency](https://img.shields.io/badge/By_Currency-{currencies_count}-yellow)]({relative_path}by_currency/)")
    badges.append(f"[![By Organization](https://img.shields.io/badge/By_Organization-{orgs_count}-orange)]({relative_path}by_org/)")
    
    if conversion_rates_count > 0:
        badges.append(f"[![Currency Prices](https://img.shields.io/badge/Currency_Prices-{conversion_rates_count}-purple)]({relative_path}currency_prices.md)")
    
    return " ".join(badges)
