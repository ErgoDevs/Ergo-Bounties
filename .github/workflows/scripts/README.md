# Bounty Finder

This script finds and processes bounties from GitHub repositories and organizations, generating various markdown files with bounty information.

## Code Structure

The code has been modularized for better maintainability:

- `bounty_finder.py`: Main script that orchestrates the process
- `run_bounty_finder.py`: Wrapper script to run the bounty finder
- `tests/`: Directory containing test scripts
  - `test_gold_price.py`: Test script for gold price functionality
  - `test_api.py`: Test script for API functionality
  - `test_config.py`: Test script for configuration functionality
- `bounty_modules/`: Directory containing the modules
  - `api_client.py`: Functions for GitHub API interactions
  - `config.py`: Configuration handling
  - `conversion_rates.py`: Functions for fetching and handling currency conversion rates
  - `extractors.py`: Functions for extracting bounty information from issues
  - `processor.py`: Data processing functionality
  - `utils.py`: Utility functions used across the codebase
  - `generators/`: Directory containing generator modules
    - `language_generator.py`: Functions for generating language-specific files
    - `organization_generator.py`: Functions for generating organization-specific files
    - `currency_generator.py`: Functions for generating currency-specific files
    - `summary_generator.py`: Functions for generating summary files
    - `readme_updater.py`: Functions for updating the README.md file

## Generated Files

The script generates the following files:

- `bounties/all.md`: Main file with summary and detailed bounties
- `bounties/summary.md`: Summary file for README reference
- `bounties/featured_bounties.md`: Featured bounties for README
- `bounties/currency_prices.md`: Table of currency prices
- `bounties/by_language/`: Directory with language-specific files
- `bounties/by_org/`: Directory with organization-specific files
- `bounties/by_currency/`: Directory with currency-specific files

## Running the Script

To run the script, use one of the following methods:

### Method 1: Using the wrapper script (recommended)

```bash
cd .github/workflows/scripts
python run_bounty_finder.py
```

### Method 2: Running the main script directly

```bash
cd .github/workflows/scripts
python bounty_finder.py
```

The script requires a GitHub token to be set as an environment variable:

```bash
export GITHUB_TOKEN=your_github_token
```

### Running Tests

To run the tests:

```bash
cd .github/workflows/scripts
python -m tests.test_gold_price  # Gold price tests
python -m tests.test_api         # API tests
python -m tests.test_config      # Configuration tests
```

### Running from GitHub Actions

The script is designed to be run from GitHub Actions, where the GITHUB_TOKEN is automatically provided.

## Configuration

The script reads configuration from:

- `bounties/tracked_repos.json`: List of repositories to track
- `bounties/tracked_orgs.json`: List of organizations to track
