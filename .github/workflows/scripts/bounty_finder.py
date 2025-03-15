#!/usr/bin/env python3
"""
Bounty Finder - Main script for finding and processing bounties from GitHub.

This script orchestrates the process of:
1. Loading configuration
2. Fetching conversion rates
3. Processing repositories and organizations
4. Generating markdown files with bounty information
"""

import sys
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bounty_finder')

# Import modules
from bounty_modules.config import BountyConfig
from bounty_modules.conversion_rates import get_conversion_rates
from bounty_modules.processor import BountyProcessor
from bounty_modules.utils import ensure_directory
from bounty_modules.generators import (
    generate_language_files,
    generate_organization_files,
    generate_currency_files,
    generate_price_table,
    generate_main_file,
    generate_summary_file,
    generate_featured_bounties_file,
    update_readme_table,
    update_ongoing_programs_table
)

def main():
    """Main function to run the bounty finder."""
    logger.info("Starting bounty finder")
    
    # Initialize configuration
    bounties_dir = 'bounties'
    config = BountyConfig(bounties_dir)
    
    # Check if configuration is valid
    if not config.is_valid():
        logger.error("Invalid configuration")
        sys.exit(1)
    
    # Ensure bounties directory exists
    ensure_directory(bounties_dir)
    
    # Load repositories and organizations
    repos_to_query = config.load_tracked_repos()
    orgs_to_query = config.load_tracked_orgs()
    
    # Fetch conversion rates
    logger.info("Fetching conversion rates")
    conversion_rates = get_conversion_rates()
    
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
    
    # Group data
    languages = processor.group_by_language()
    orgs = processor.group_by_organization()
    currencies_dict = processor.group_by_currency()
    
    # Generate output files
    logger.info("Generating output files")
    
    # Generate language-specific files
    generate_language_files(
        bounty_data, 
        languages, 
        conversion_rates, 
        total_bounties, 
        len(currencies_dict), 
        len(orgs), 
        bounties_dir
    )

    # Generate organization-specific files
    generate_organization_files(
        bounty_data, 
        orgs, 
        conversion_rates, 
        total_bounties, 
        languages, 
        len(currencies_dict), 
        bounties_dir
    )

    # Generate currency-specific files
    generate_currency_files(
        bounty_data, 
        currencies_dict, 
        conversion_rates, 
        total_bounties, 
        languages, 
        orgs, 
        bounties_dir
    )

    # Generate currency price table
    generate_price_table(
        conversion_rates, 
        total_bounties, 
        languages, 
        currencies_dict, 
        orgs, 
        bounties_dir
    )

    # Generate main file
    generate_main_file(
        bounty_data, 
        project_totals, 
        languages, 
        currencies_dict, 
        orgs, 
        conversion_rates, 
        total_bounties, 
        total_value, 
        bounties_dir
    )
    
    # Update ongoing programs table
    update_ongoing_programs_table(
        bounty_data,
        bounties_dir
    )

    # Generate summary file
    generate_summary_file(
        project_totals, 
        languages, 
        currencies_dict, 
        orgs, 
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
        languages, 
        currencies_dict, 
        orgs, 
        bounties_dir
    )
    
    # Update the README.md table and badges with the latest bounty counts and values
    update_readme_table(
        total_bounties,
        total_value,
        bounties_dir,
        len(languages),
        len(currencies_dict),
        len(orgs),
        len(conversion_rates),
        languages=languages,
        bounty_data=bounty_data,
        conversion_rates=conversion_rates
    )

    # Print summary
    logger.info(f"Total bounties found: {total_bounties}")
    logger.info(f"Total ERG equivalent value: {total_value:.2f}")
    logger.info("Bounty finder completed successfully")

if __name__ == "__main__":
    main()
