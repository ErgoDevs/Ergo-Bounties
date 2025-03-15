"""
Module for updating the README.md file with bounty information.

This script generates and updates the main README.md file with:
- Current bounty statistics (counts, values)
- Language badges and counts
- Navigation links to different sections
- Featured and high-value bounty highlights
"""

import re
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging with more detailed format
logger = logging.getLogger('readme_updater')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def load_config() -> Dict:
    """
    Load configuration from config.json file.
    
    Returns:
        Dict: Configuration dictionary
    """
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration from {config_path}: {e}")
        # Return default configuration
        return {
            "readme": {
                "display_beginner_friendly": True,
                "display_high_value": True,
                "high_value_threshold_erg": 1000,
                "beginner_friendly_labels": ["beginner", "beginner-friendly", "good first issue"]
            },
            "badges": {
                "colors": {
                    "open_bounties": "4CAF50",
                    "total_value": "2196F3",
                    "high_value": "FFC107",
                    "featured": "9C27B0"
                }
            },
            "template_vars": {
                "default_repos_count": 18,
                "update_time": "Midnight UTC"
            }
        }

def update_readme_table(
    total_bounties: int, 
    total_value: float, 
    bounties_dir: str, 
    languages_count: int = 0, 
    currencies_count: int = 0, 
    orgs_count: int = 0, 
    conversion_rates_count: int = 0,
    languages: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    bounty_data: Optional[List[Dict[str, Any]]] = None,
    conversion_rates: Optional[Dict[str, float]] = None
) -> bool:
    """
    Update the Featured Bounties table and badges in the README.md file.
    
    Args:
        total_bounties: Total number of bounties
        total_value: Total value of bounties in ERG
        bounties_dir: Bounties directory
        languages_count: Number of languages
        currencies_count: Number of currencies
        orgs_count: Number of organizations
        conversion_rates_count: Number of conversion rates
        languages: Dictionary of languages and their bounties (optional)
        bounty_data: List of all bounty data (optional)
        conversion_rates: Dictionary of currency conversion rates (optional)
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    logger.info("Updating README.md table and badges")
    
    # Load configuration
    config = load_config()
    
    # Use project relative path for better portability
    readme_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..', 'README.md'))
    logger.info(f"Using README.md path: {readme_file}")
    
    try:
        # Read the current README.md file
        with open(readme_file, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        
        # Load constants from constants.json
        constants_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'constants.json')
        try:
            with open(constants_path, 'r', encoding='utf-8') as f:
                constants = json.load(f)
                logger.info(f"Loaded constants from {constants_path}")
        except Exception as e:
            logger.error(f"Error loading constants from {constants_path}: {e}")
            # Create default constants rather than raising an exception
            constants = {
                "language_colors": {
                    "Scala": "DC322F",
                    "Rust": "DEA584",
                    "JavaScript": "F7DF1E",
                    "TypeScript": "3178C6",
                    "Python": "3776AB",
                    "Java": "007396"
                },
                "fixed_bounties": {
                    "fleet_sdk": {"count": 0, "amount": 0, "currency": "SigUSD"},
                    "keystone": {"count": 0, "amount": 0, "currency": "ERG"}
                }
            }
            logger.warning("Using default constants due to error")
        
        # Get the current date
        current_date = datetime.now().strftime("%b %d, %Y")
        
        # Validate inputs to avoid potential errors
        if not isinstance(total_bounties, int) or total_bounties < 0:
            logger.error(f"Invalid total_bounties value: {total_bounties}")
            total_bounties = 0
            
        if not isinstance(total_value, (int, float)) or total_value < 0:
            logger.error(f"Invalid total_value: {total_value}")
            total_value = 0.0
        
        # Create the new table row for the current date
        new_row = f"| {current_date} | {total_bounties} | **{total_value:,.2f} ERG**|"
        
        # Get fixed bounties from constants with error handling
        fleet_sdk = constants.get("fixed_bounties", {}).get("fleet_sdk", {"count": 0, "amount": 0, "currency": "SigUSD"})
        keystone = constants.get("fixed_bounties", {}).get("keystone", {"count": 0, "amount": 0, "currency": "ERG"})
        
        # Calculate the new total (fixed values + dynamic value)
        fleet_count = fleet_sdk.get("count", 0)
        keystone_count = keystone.get("count", 0)
        keystone_amount = keystone.get("amount", 0)
        
        total_count = total_bounties + fleet_count + keystone_count
        total_erg_value = total_value + keystone_amount  # Keystone is in ERG
        
        # Create the new total row
        new_total_row = f"| **Total**                   | **{total_count}**     | **{total_erg_value:,.2f} ERG**|"
        
        # Find the table in the README.md file and update the third row and total row
        table_pattern = r"\| Week\s*\|\s*(?:Count of Open Issues|Open Issues)\s*\|\s*(?:ERG Bounties|Rewards)\s*\|\s*\n\|[-\s|]*\n\|[^\n]*\n\|[^\n]*\n\|[^\n]*\n\|[^\n]*\n"
        
        # Create the replacement table using values from constants
        replacement_table = f"""| Week                        | Open Issues | Rewards         |
|-----------------------------|-------------|-----------------|
| Keystone Wallet Integration | [Last Update](https://discord.com/channels/668903786361651200/669989266478202917/1344310506277830697) | **{keystone["amount"]:,} {keystone["currency"]}**   |
| [Fleet SDK Tutorials](https://github.com/fleet-sdk/docs/issues/8) | {fleet_sdk["count"]}           | **{fleet_sdk["amount"]} {fleet_sdk["currency"]}**  |
| {current_date}                | {total_bounties}         | **{total_value:,.2f} ERG**|
| **Total**                   | **{total_count}**     | **{total_erg_value:,.2f} ERG**|"""
        
        # Instead of updating an existing README, we'll generate a completely new one
        # with the desired format, while preserving the dynamic badge updates
        
        # Get language colors from constants (with fallback)
        language_colors = constants.get("language_colors", {})
        
        # Use the languages parameter to get language counts
        language_counts = {}
        if languages:
            language_counts = {lang: len(bounties) for lang, bounties in languages.items()}
        
        # Calculate high value bounty count if bounty_data and conversion_rates are provided
        # Get configuration values with defaults
        high_value_threshold = config.get("readme", {}).get("high_value_threshold_erg", 1000)
        beginner_friendly_labels = config.get("readme", {}).get("beginner_friendly_labels", 
                                                                ["beginner", "beginner-friendly", "good first issue"])
        badge_colors = config.get("badges", {}).get("colors", {})
        update_time = config.get("template_vars", {}).get("update_time", "Midnight UTC")
        default_repos_count = config.get("template_vars", {}).get("default_repos_count", 18)
        
        high_value_count = 0
        beginner_bounty_count = 0
        
        if bounty_data and conversion_rates:
            try:
                # Try to import the calculate_erg_value function
                try:
                    from ..utils import calculate_erg_value
                except ImportError:
                    # Define a basic implementation if import fails
                    def calculate_erg_value(amount, currency, rates):
                        if currency == "ERG":
                            return float(amount)
                        elif currency in rates:
                            return float(amount) * rates.get(currency, 0)
                        return 0
                
                # Count bounties with value over the high_value_threshold
                for bounty in bounty_data:
                    # Get amount and currency with safe fallbacks
                    amount = bounty.get("amount", "Not specified")
                    currency = bounty.get("currency", "Not specified")
                    
                    # Check for beginner-friendly
                    labels = bounty.get("labels", [])
                    if any(label.lower() in beginner_friendly_labels for label in labels):
                        beginner_bounty_count += 1
                    
                    if amount != "Not specified":
                        try:
                            # Calculate ERG value
                            erg_value = calculate_erg_value(amount, currency, conversion_rates)
                            if erg_value >= high_value_threshold:
                                high_value_count += 1
                        except (ValueError, TypeError):
                            pass
                
                logger.info(f"Found {high_value_count} high value bounties (>= {high_value_threshold} ERG)")
                logger.info(f"Found {beginner_bounty_count} beginner-friendly bounties")
            except Exception as e:
                logger.error(f"Error calculating high value bounties: {e}")
        
        
        # Generate language badges HTML - sorted by count (highest first)
        language_badges = ""
        for lang, count in sorted(language_counts.items(), key=lambda x: x[1], reverse=True):
            if count > 0:  # Only show languages with bounties
                color = language_colors.get(lang, "DC322F")
                # URL encode special characters in language name
                encoded_lang = lang.replace(" ", "%20").replace("+", "%2B").replace("#", "%23")
                language_badges += f'    <a href="/bounties/by_language/{lang.lower()}.md"><img src="https://img.shields.io/badge/{encoded_lang}-{count}-{color}"></a>\n'
        
        # Count repositories from tracked_repos.json and tracked_orgs.json
        repos_count = 0
        try:
            # Count repos from tracked_repos.json
            repos_file = f'{bounties_dir}/tracked_repos.json'
            try:
                with open(repos_file, 'r', encoding='utf-8') as f:
                    repos = json.load(f)
                    repos_count += len(repos)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.error(f"Error reading tracked_repos.json: {e}")
            
            # Count repos from tracked_orgs.json
            orgs_file = f'{bounties_dir}/tracked_orgs.json'
            try:
                with open(orgs_file, 'r', encoding='utf-8') as f:
                    orgs = json.load(f)
                    repos_count += len(orgs) * 5  # Estimate 5 repos per org on average
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.error(f"Error reading tracked_orgs.json: {e}")
        except Exception as e:
            logger.error(f"Error counting repositories: {e}")
            repos_count = default_repos_count  # Fallback to the default repos count from config
        
        # Create the new README content with improved formatting and additional sections
        new_readme = f'''<div align="center">
  <h1>🏆 Ergo Ecosystem Bounties</h1>
  <p><em>The Central Hub for Discovering, Claiming, and Managing Ergo Bounties</em></p>

  <p>
    <a href="/bounties/all.md">
      <img src="https://img.shields.io/badge/Open%20Bounties-{total_bounties}%2B-{badge_colors.get('open_bounties', '4CAF50')}" alt="Open Bounties">
    </a>
    <a href="/bounties/summary.md">
      <img src="https://img.shields.io/badge/💰%20Total%20Value-{total_erg_value:,.2f}%20ERG-{badge_colors.get('total_value', '2196F3')}" alt="Total Value">
    </a>
    <a href="/bounties/all.md">
      <img src="https://img.shields.io/badge/🌟%20High%20Value-{high_value_count}%2B%20Over%20{high_value_threshold}%20ERG-{badge_colors.get('high_value', 'FFC107')}" alt="High Value Bounties">
    </a>
    <a href="/bounties/featured_bounties.md">
      <img src="https://img.shields.io/badge/🔥%20Featured%20Bounties-{badge_colors.get('featured', '9C27B0')}" alt="Featured Bounties">
    </a>
  </p>

  <h2>🚀 Get Started</h2>
  
  <p><em>Find, claim, and contribute to Ergo ecosystem bounties across {repos_count}+ indexed repositories</em></p>

  <p>
    <a href="/bounties/all.md">
      <img src="https://img.shields.io/badge/✅%20Browse%20Bounties-3F51B5" alt="Browse Bounties">
    </a>
    <a href="/docs/bounty-submission-guide.md#reserving-a-bounty">
      <img src="https://img.shields.io/badge/🔒%20Reserve-green" alt="Reserve a Bounty">
    </a>
    <a href="/docs/bounty-submission-guide.md#step-by-step-submission-process">
      <img src="https://img.shields.io/badge/💰%20Request%20Payment-orange" alt="Request Payment">
    </a>
    <a href="/docs/add-missing-bounty-guide.md">
      <img src="https://img.shields.io/badge/➕%20Add%20Bounty-red" alt="Add a New Bounty">
    </a>
  </p>

  <h2>📚 Explore Bounties by Category</h2>

  <div>
    <h3>🔤 By Programming Language</h3>
    <p>
      {language_badges.rstrip()}
      <a href="/bounties/by_language/">
        <img src="https://img.shields.io/badge/🌐%20All%20Languages-purple" alt="All Languages">
      </a>
    </p>
  </div>

  <div>
    <h3>💵 By Currency</h3>
    <p>
      <a href="/bounties/by_currency/erg.md">
        <img src="https://img.shields.io/badge/ERG-Ergo-orange" alt="ERG">
      </a>
      <a href="/bounties/by_currency/sigusd.md">
        <img src="https://img.shields.io/badge/SigUSD-Stablecoin-blue" alt="SigUSD">
      </a>
      <a href="/bounties/by_currency/">
        <img src="https://img.shields.io/badge/🌐%20All%20Currencies-purple" alt="All Currencies">
      </a>
    </p>
  </div>

  <div>
    <h3>🏢 By Organization</h3>
    <p>
      <a href="/bounties/by_org/">
        <img src="https://img.shields.io/badge/🌐%20All%20Organizations-purple" alt="All Organizations">
      </a>
    </p>
  </div>

  <h2>👨‍💻 For Developers</h2>

  <p>
    <a href="/bounties/all.md?filter=beginner">
      <img src="https://img.shields.io/badge/🔰%20Beginner%20Friendly-{beginner_bounty_count}-28A745" alt="Beginner Friendly">
    </a>
    <a href="/docs/ongoing-programs.md">
      <img src="https://img.shields.io/badge/📋%20Ongoing%20Programs-FF5722" alt="Ongoing Programs">
    </a>
  </p>

  <h2>⚙️ Automation & Maintenance</h2>

  <p><em>This repository is updated daily at {update_time} via GitHub Actions</em></p>

  <p>
    <a href="/bounties/currency_prices.md">
      <img src="https://img.shields.io/badge/💹%20Current%20Rates-00BCD4" alt="Currency Rates">
    </a>
    <a href="/docs/how-it-works.md">
      <img src="https://img.shields.io/badge/🔧%20How%20It%20Works-795548" alt="How It Works">
    </a>
    <a href="/docs/donate.md">
      <img src="https://img.shields.io/badge/❤️%20Donate-F44336" alt="Donate">
    </a>
    <a href="https://github.com/ergoplatform/Ergo-Bounties">
      <img src="https://img.shields.io/badge/⭐%20Star%20on%20GitHub-333333" alt="Star on GitHub">
    </a>
  </p>
</div>

<!-- Latest Update: {datetime.now().strftime("%Y-%m-%d")} -->

'''
        
        # Use the new README content
        updated_readme = new_readme
        
        # Write the updated README.md file
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(updated_readme)
            
        logger.info("Updated README.md with new bounty counts, values, and badges")
        return True
    except Exception as e:
        logger.error(f"Error updating README.md: {e}")
        return False

def safe_load_json(file_path: str) -> Tuple[bool, Union[Dict, List, None]]:
    """
    Safely load a JSON file with robust error handling.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Tuple of (success, data)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return True, data
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return False, None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {file_path}")
        return False, None
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return False, None
