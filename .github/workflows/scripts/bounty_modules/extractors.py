import re
import logging
from typing import List, Dict, Tuple, Optional, Any, Union

# Configure logging
logger = logging.getLogger('extractors')

def check_bounty_labels(labels: List[Dict[str, Any]]) -> bool:
    """
    Check if any label contains 'bounty' or 'b-'.
    
    Args:
        labels: List of label objects from GitHub API
        
    Returns:
        True if any label contains 'bounty' or 'b-'
    """
    return any("bounty" in label['name'].lower() or "b-" in label['name'].lower() for label in labels)

def extract_bounty_from_labels(labels: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract bounty amount and currency from issue labels.
    
    Args:
        labels: List of label objects from GitHub API
        
    Returns:
        Tuple of (amount, currency) or (None, None) if not found
    
    Examples:
        - "bounty-100erg" -> ("100", "ERG")
        - "b-50sigusd" -> ("50", "SigUSD")
        - "bounty-2g gold" -> ("2", "g GOLD")
    """
    # Define regex patterns for different bounty formats
    label_patterns = [
        # Cryptocurrency patterns
        r'bounty\s*-?\s*(\d+)\s*(sigusd|rsn|bene|erg|gort)',
        r'b-(\d+)\s*(sigusd|rsn|bene|erg|gort)',
        r'(\d+)\s*(sigusd|rsn|bene|erg|gort)\s*bounty',
        # Precious metals patterns
        r'bounty\s*-?\s*(\d+(?:\.\d+)?)\s*(gram|g|oz|ounce)s?\s+(?:of\s+)?(gold|silver|platinum)',
        r'(\d+(?:\.\d+)?)\s*(gram|g|oz|ounce)s?\s+(?:of\s+)?(gold|silver|platinum)\s*bounty'
    ]
    
    for label in labels:
        label_name = label['name'].lower()
        logger.debug(f"Checking label: {label_name}")
        
        for pattern in label_patterns:
            match = re.search(pattern, label_name, re.IGNORECASE)
            if match:
                if match.groups()[-1] in ['gold', 'silver', 'platinum']:
                    # Handle precious metals format
                    amount = match.group(1)
                    unit = match.group(2).lower()
                    metal = match.group(3).upper()
                    
                    # Normalize unit names
                    unit = {
                        'gram': 'g',
                        'g': 'g',
                        'oz': 'oz',
                        'ounce': 'oz'
                    }.get(unit, unit)
                    
                    logger.info(f"Found bounty in label: {amount} {unit} {metal}")
                    return amount, f"{unit} {metal}"
                else:
                    # Handle cryptocurrency format
                    amount = match.group(1)
                    currency = match.group(2).upper()
                    if currency == 'SIGUSD':
                        currency = 'SigUSD'
                    
                    logger.info(f"Found bounty in label: {amount} {currency}")
                    return amount, currency
    
    logger.debug("No bounty found in labels")
    return None, None

def extract_bounty_from_text(title: str, body: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract bounty amount and currency from issue title and body.
    
    Args:
        title: Issue title
        body: Issue body
        
    Returns:
        Tuple of (amount, currency) or (None, None) if not found
    
    Examples:
        - "Bounty: $100" -> ("100", "USD")
        - "50 ERG bounty" -> ("50", "ERG")
        - "Bounty: 2g of GOLD" -> ("2", "g GOLD")
    """
    # Define regex patterns for different bounty formats in text
    patterns = [
        r'bounty:?\s*[\$€£]?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(sigusd|gort|rsn|bene|erg|usd|ergos?|dollars?|€|£|\$)?',
        r'[\$€£]\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:sigusd|gort|rsn|bene|erg|usd|ergos?|bounty)',
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(sigusd|gort|rsn|bene|erg|usd|ergos?)\s*bounty',
        r'bounty:?\s*(\d+(?:\.\d+)?)\s*(gram|g|oz|ounce)s?\s+(?:of\s+)?(gold|silver|platinum)',
        r'(\d+(?:\.\d+)?)\s*(gram|g|oz|ounce)s?\s+(?:of\s+)?(gold|silver|platinum)\s*bounty'
    ]
    
    # Combine title and body for searching
    text = f"{title} {body}".lower()
    logger.debug(f"Searching for bounty in text (length: {len(text)})")
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) == 3 and match.group(3) in ['gold', 'silver', 'platinum']:
                # Handle precious metals format
                amount = match.group(1)
                unit = match.group(2).lower()
                metal = match.group(3).upper()
                
                # Normalize unit names
                unit = {
                    'gram': 'g',
                    'g': 'g',
                    'oz': 'oz',
                    'ounce': 'oz'
                }.get(unit, unit)
                
                logger.info(f"Found bounty in text: {amount} {unit} {metal}")
                return amount, f"{unit} {metal}"
            else:
                # Handle cryptocurrency/fiat format
                amount = match.group(1).replace(',', '')
                currency = match.group(2) if len(match.groups()) > 1 and match.group(2) else 'USD'
                
                # Normalize currency names
                currency = {
                    '$': 'USD',
                    '€': 'EUR',
                    '£': 'GBP',
                    'dollars': 'USD',
                    'erg': 'ERG',
                    'ergos': 'ERG',
                    'sigusd': 'SigUSD',
                    'rsn': 'RSN',
                    'bene': 'BENE',
                    'gort': 'GORT'
                }.get(currency.lower(), currency.upper())
                
                logger.info(f"Found bounty in text: {amount} {currency}")
                return amount, currency
    
    logger.debug("No bounty found in text")
    return None, None
