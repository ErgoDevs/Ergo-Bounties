#!/usr/bin/env python3
"""
Ergo Bounty Finder - Main Application

This script is the main entry point for the Ergo Bounty Finder application. It orchestrates:
1. Loading configuration and API tokens
2. Fetching conversion rates for currencies
3. Processing GitHub repositories and organizations to find bounties
4. Generating markdown files with bounty information

The application runs automatically via GitHub Actions, but can also be run manually
for testing and development purposes.
"""

import sys
import os
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bounty_finder')

# Import modules
from src.core.config import BountyConfig
from src.api.currency_client import CurrencyClient
from src.core.processor import BountyProcessor
from src.utils.common import ensure_directory
from src.generators.main import (
    generate_language_files,
    generate_organization_files,
    generate_currency_files,
    generate_price_table,
    generate_main_file,
    generate_summary_file,
    generate_featured_bounties_file,
    generate_bounty_discovery_files,
    update_readme_badges,
    update_ongoing_programs_table,
    generate_high_value_bounties_file,
    # Import moved functions needed for badge update
    find_high_value_bounties,
    group_by_language
)

def main():
    """Main function to run the bounty finder."""
    logger.info("Starting bounty finder")
    
    # Initialize configuration
    bounties_dir = 'data'
    config = BountyConfig(bounties_dir)
    
    # Check if configuration is valid
    if not config.is_valid():
        logger.error("Invalid configuration")
        sys.exit(1)
    
    # Ensure bounties directory and subdirectories exist
    config.ensure_directories()
    
    # Load repositories and organizations
    repos_to_query = config.load_tracked_repos()
    orgs_to_query = config.load_tracked_orgs()
    
    # Fetch conversion rates
    logger.info("Fetching conversion rates")
    currency_client = CurrencyClient()
    conversion_rates = currency_client.get_all_rates()
    
    # Initialize processor
    processor = BountyProcessor(config.github_token, conversion_rates)
    
    # Process organizations to find repositories
    repos_to_query = processor.process_organizations(orgs_to_query, repos_to_query)
    
    # Process repositories to find bounties
    logger.info(f"Processing {len(repos_to_query)} repositories")
    processor.process_repositories(repos_to_query)
    
    # Load and add extra bounties from extra_bounties.json
    logger.info("Loading extra bounties")
    extra_bounties = config.load_extra_bounties()
    if extra_bounties:
        logger.info(f"Adding {len(extra_bounties)} extra bounties")
        processor.add_extra_bounties(extra_bounties)
    
    # Get processed data
    bounty_data = processor.get_bounty_data()
    project_totals = processor.get_project_totals()
    total_bounties, total_value = processor.get_total_stats()
    
    # No need to group data here anymore, generators handle it
    
    # Generate output files
    logger.info("Generating output files")
    
    # Generate language-specific files
    generate_language_files(
        bounty_data,
        conversion_rates,
        total_bounties,
        bounties_dir
    )

    # Generate organization-specific files
    generate_organization_files(
        bounty_data,
        conversion_rates,
        total_bounties,
        bounties_dir
    )

    # Generate currency-specific files
    generate_currency_files(
        bounty_data,
        conversion_rates,
        total_bounties,
        bounties_dir
    )

    # Generate currency price table
    generate_price_table(
        bounty_data, # Pass bounty_data now
        conversion_rates,
        total_bounties,
        bounties_dir
    )

    # Generate main file
    generate_main_file(
        bounty_data,
        conversion_rates,
        total_bounties,
        bounties_dir
    )

    # Update ongoing programs table
    update_ongoing_programs_table(
        bounty_data,
        conversion_rates,
        bounties_dir
    )

    # Generate summary file
    generate_summary_file(
        bounty_data, # Pass bounty_data now
        project_totals,
        conversion_rates,
        total_bounties,
        total_value,
        bounties_dir
    )

    # Generate featured bounties file
    generate_featured_bounties_file(
        bounty_data,
        conversion_rates,
        total_bounties,
        total_value,
        # Pass the necessary arguments based on the updated function signature
        # languages_dict, # Not needed directly by this generator anymore
        # currencies_dict, # Not needed directly by this generator anymore
        # orgs_dict, # Not needed directly by this generator anymore
        bounties_dir
    )

    # Generate high-value bounties file
    generate_high_value_bounties_file(
        bounty_data,
        conversion_rates,
        total_bounties,
        # total_value, # Removed (not needed by generator)
        # languages, # Removed
        # currencies_dict, # Removed
        # orgs, # Removed
        bounties_dir,
        high_value_threshold=1000
    )

    generate_bounty_discovery_files(
        bounty_data,
        conversion_rates,
        total_bounties,
        bounties_dir
    )

    # Update the README.md badges with the latest bounty counts and values
    # Need to get high_value_bounties count and languages dict now
    high_value_bounties_list = find_high_value_bounties(bounty_data, conversion_rates, threshold=1000)
    languages_dict = group_by_language(bounty_data)
    update_readme_badges(
        total_bounties,
        total_value,
        len(high_value_bounties_list),
        languages_dict # Pass the generated dict
    )

    # Print summary
    logger.info(f"Total bounties found: {total_bounties}")
    logger.info(f"Total ERG equivalent value: {total_value:.2f}")
    logger.info("Bounty finder completed successfully")

if __name__ == "__main__":
    main()
