#!/usr/bin/env python3
"""
Test script for configuration functionality.
This combines functionality from:
- test_json_files.py
"""

import sys
import os
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_config')

# Add the parent directory to the path so Python can find the bounty_modules package
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from bounty_modules.config import BountyConfig

def test_json_files():
    """
    Test reading the JSON configuration files
    """
    logger.info("Testing JSON configuration files")
    
    # Get the absolute path to the repository root
    repo_root = os.path.abspath(os.path.join(parent_dir, "../.."))
    logger.info(f"Repository root: {repo_root}")
    
    bounties_dir = os.path.join(repo_root, "bounties")
    repos_path = os.path.join(bounties_dir, "tracked_repos.json")
    orgs_path = os.path.join(bounties_dir, "tracked_orgs.json")
    
    logger.info("Checking if configuration files exist:")
    repos_exists = os.path.exists(repos_path)
    orgs_exists = os.path.exists(orgs_path)
    logger.info(f"  tracked_repos.json exists: {repos_exists}")
    logger.info(f"  tracked_orgs.json exists: {orgs_exists}")
    
    if not repos_exists or not orgs_exists:
        logger.error("One or more configuration files are missing")
        return False
    
    try:
        logger.info("Reading tracked_repos.json...")
        with open(repos_path, "r") as f:
            repos = json.load(f)
            logger.info(f"Successfully loaded {len(repos)} repositories")
            
            # Validate repository format
            if repos and isinstance(repos, list):
                sample_repo = repos[0]
                if "owner" in sample_repo and "repo" in sample_repo:
                    logger.info(f"Repository format is valid: {sample_repo}")
                else:
                    logger.error(f"Invalid repository format: {sample_repo}")
                    return False
            else:
                logger.error("Invalid repositories data format")
                return False
        
        logger.info("Reading tracked_orgs.json...")
        with open(orgs_path, "r") as f:
            orgs = json.load(f)
            logger.info(f"Successfully loaded {len(orgs)} organizations")
            
            # Validate organization format
            if orgs and isinstance(orgs, list):
                sample_org = orgs[0]
                if "org" in sample_org:
                    logger.info(f"Organization format is valid: {sample_org}")
                else:
                    logger.error(f"Invalid organization format: {sample_org}")
                    return False
            else:
                logger.error("Invalid organizations data format")
                return False
        
        return True
    except Exception as e:
        logger.error(f"Error reading configuration files: {e}")
        return False

def test_config_module():
    """
    Test the config module functionality
    """
    logger.info("Testing config module")
    
    try:
        # Initialize configuration
        config = BountyConfig()
        
        # Check if GitHub token is available
        if config.github_token:
            logger.info("GitHub token is available")
        else:
            logger.warning("GitHub token is not available")
        
        # Load repositories
        repos = config.load_tracked_repos()
        if repos:
            logger.info(f"Successfully loaded {len(repos)} repositories")
        else:
            logger.warning("No repositories loaded")
        
        # Load organizations
        orgs = config.load_tracked_orgs()
        if orgs:
            logger.info(f"Successfully loaded {len(orgs)} organizations")
        else:
            logger.warning("No organizations loaded")
        
        # Check if configuration is valid
        is_valid = config.is_valid()
        logger.info(f"Configuration is valid: {is_valid}")
        
        return is_valid
    except Exception as e:
        logger.error(f"Error testing config module: {e}")
        return False

def main():
    """Run all configuration tests"""
    logger.info("=== Configuration Testing Suite ===")
    
    # Test JSON files
    json_result = test_json_files()
    logger.info(f"JSON files test {'succeeded' if json_result else 'failed'}")
    
    # Test config module
    config_result = test_config_module()
    logger.info(f"Config module test {'succeeded' if config_result else 'failed'}")
    
    logger.info("=== Configuration Testing Complete ===")

if __name__ == "__main__":
    main()
