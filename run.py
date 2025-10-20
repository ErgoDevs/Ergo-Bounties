#!/usr/bin/env python3
"""
Wrapper script to run the Ergo Bounty Finder.
This script ensures the correct Python path setup.
"""

import os
import sys
import argparse

# Add the current directory to Python path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now we can import from our src directory
from src.bounty_finder import main

def main_with_args():
    """Run the main function with command line arguments."""
    parser = argparse.ArgumentParser(description='Run the Ergo Bounty Finder')
    parser.add_argument('--refresh', action='store_true',
                        help='Force refresh of all data files')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    args = parser.parse_args()
    
    # Set environment variables based on arguments
    if args.refresh:
        print("Force refreshing all data")
        os.environ['FORCE_REFRESH'] = 'true'
    
    if args.verbose:
        print("Enabling verbose logging")
        os.environ['VERBOSE'] = 'true'
    
    # Check for GitHub token via env or .env (CI-friendly)
    env_path = os.path.join('src', '.env')
    if not (os.environ.get('GITHUB_TOKEN') or os.path.exists(env_path)):
        print(f"ERROR: No GitHub token found. Set GITHUB_TOKEN env var (preferred in CI) or create {env_path} with 'github_token=YOUR_TOKEN'")
        print("In GitHub Actions, use: env: GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}")
        print("Create a Personal Access Token at: https://github.com/settings/tokens")
        sys.exit(1)
    
    # Run the main function from bounty_finder
    main()

if __name__ == "__main__":
    main_with_args()
