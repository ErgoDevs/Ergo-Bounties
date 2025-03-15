# 🤖 Ergo Bounties: How It Works

This document explains the technical details of how the Ergo Ecosystem Bounties repository automatically tracks, updates, and displays bounties across the Ergo blockchain ecosystem.

## Automated Bounty Tracking System

The repository uses GitHub Actions to automatically track and update the list of open bounties from various projects in the Ergo ecosystem.

### Automation Schedule

- **Daily Updates**: The bounty list is refreshed every day at midnight UTC
- **On-Demand Updates**: Triggered whenever `tracked_repos.json` is modified
- **Manual Trigger**: Maintainers can manually run the workflow when needed

### How It Works

The automation process follows these steps:

1. **Repository Scanning**: The system scans all repositories listed in `tracked_repos.json`
2. **Issue Identification**: It identifies issues with bounty tags or mentions in their title or description
3. **Bounty Extraction**: The system extracts bounty amounts and currencies using pattern matching
4. **Value Calculation**: Where possible, it converts different currencies to ERG equivalent values
5. **Report Generation**: It generates updated bounty reports in various formats and categories
6. **Automatic Commit**: Changes are committed back to the repository

## Adding Repositories to Tracking

To add a new repository to the tracking system:

1. Fork this repository
2. Edit the `tracked_repos.json` file to add the new repository
   ```json
   {"owner": "repo-owner", "repo": "repo-name"}
   ```
3. Submit a PR with title: `[ADD REPO] owner/repo-name`

Once merged, the automation will include the new repository's bounties in the next update.

## Adding Manual Bounties

For bounties that aren't in GitHub repositories or don't follow standard formats:

1. Fork this repository
2. Edit the `extra_bounties.json` file to add the new bounty:
   ```json
   {
     "timestamp": "YYYY-MM-DD HH:MM:SS",
     "owner": "organization-name",
     "repo": "project-name",
     "title": "Bounty Title",
     "url": "https://link-to-bounty-details",
     "amount": "100",
     "currency": "ERG",
     "primary_lang": "Language",
     "secondary_lang": "None",
     "labels": ["bounty", "manual-entry"],
     "issue_number": "ext-123",
     "creator": "your-username"
   }
   ```
3. Submit a PR with title: `[ADD MANUAL BOUNTY] Bounty Title`

The system will automatically include these manual bounties alongside GitHub-sourced bounties in all listings.

## Bounty Detection Logic

The system identifies bounties using several methods:

### Label-Based Detection

Issues with labels containing "bounty" or "b-" are automatically included. The system also extracts bounty amounts from labels with patterns like:
- `bounty-100-erg`
- `b-500-sigusd`
- `100-erg-bounty`

### Content-Based Detection

If no bounty information is found in labels, the system searches the issue title and body for patterns like:
- `bounty: 100 ERG`
- `$500 bounty`
- `200 SigUSD bounty`

### Currency Support

The system recognizes multiple currencies:
- ERG (Ergo's native token)
- SigUSD (Ergo's stablecoin)
- RSN (Rosen Bridge token)
- BENE (Benefaction token)
- GORT (Governance token)
- Precious metals (g GOLD, etc.)

## Technical Implementation

The bounty tracking is implemented in Python using the GitHub API. The main components are:

- **GitHub Actions Workflow**: Defined in `.github/workflows/update-bounties.yml`
- **Python Script**: Located at `scrape/bounty_finder_github_action.py`
- **Repository List**: Maintained in `tracked_repos.json`

### GitHub API Usage

The script uses the GitHub API to:
- Fetch repository language information
- Retrieve open issues from tracked repositories
- Extract issue details including labels, title, and body

### Output Files

The system generates:
- A Markdown file (`bounty_issues.md`) with a formatted table of all bounties
- A CSV file (`scrape/bounty_issues_TIMESTAMP.csv`) with detailed bounty data
- Language-specific Markdown files in the `bounties/by_language/` directory
- Currency-specific Markdown files in the `bounties/by_currency/` directory
- Organization-specific Markdown files in the `bounties/by_org/` directory
- Summary statistics including total counts and values

## For Developers

This section provides information for developers who want to contribute to the Ergo Bounties codebase.

### Code Organization

The repository code is structured as follows:

```
.github/workflows/         # GitHub Actions workflow files 
└── scripts/               # Scripts used by GitHub Actions
    ├── bounties/          # Generated bounty reports & data
    ├── bounty_modules/    # Core code modules
    │   └── generators/    # Report and README generators
    │       ├── config.json       # Configuration for README generator
    │       └── readme_updater.py # README generation script
    └── constants.json     # Configuration constants
```

### Key Components for Developers

#### 1. README Generator (`readme_updater.py`)

This module is responsible for updating the main README.md. Its key features include:

- Loading configurations from `config.json` and `constants.json`
- Generating language badges based on current bounty counts
- Calculating statistics (high-value bounties, beginner-friendly counts)
- Formatting dynamic sections based on current data
- Robust error handling with fallbacks

#### 2. Configuration System

Two main configuration files control the system behavior:

##### `constants.json`
Contains project-wide constants like:
```json
{
  "language_colors": { "Scala": "DC322F", "Rust": "DEA584" },
  "fixed_bounties": {
    "fleet_sdk": { "count": 7, "currency": "SigUSD", "amount": 775 },
    "keystone": { "count": 1, "currency": "ERG", "amount": 3000 }
  }
}
```

##### `config.json`
Controls the README generator specifically:
```json
{
  "readme": {
    "section_order": ["header", "stats_badges", "get_started"],
    "display_beginner_friendly": true,
    "high_value_threshold_erg": 1000
  },
  "badges": {
    "colors": { "open_bounties": "4CAF50", "total_value": "2196F3" }
  }
}
```

### Development Best Practices

When modifying the codebase, follow these guidelines:

1. **Error Handling**: Always include robust error handling with fallbacks for missing data
2. **Configuration-Driven**: Make features configurable rather than hardcoded
3. **Type Annotations**: Use proper Python type hints for better maintainability
4. **Modular Design**: Keep functions focused and modular for easier testing
5. **Backward Compatibility**: Ensure changes don't break existing functionality

### Testing Changes

To test changes to the scripts:

1. Run the scripts locally with appropriate test data
2. Check that generated files match expected formats
3. Verify error handling by deliberately introducing bad input
4. Test with various configurations to ensure flexibility
5. Run the test.py script to validate full system functionality

## Limitations and Edge Cases

- **Currency Conversion**: The system uses approximate conversion rates for non-ERG currencies
- **Manual Bounties**: Some bounties may not follow standard formats and require manual addition
- **API Rate Limits**: The GitHub API has rate limits that may affect large scans
- **Pattern Matching**: Complex or unusual bounty descriptions may not be correctly parsed

## Future Improvements

Planned enhancements to the system include:
- More accurate currency conversion rates
- Better categorization of bounties by type or difficulty
- Enhanced statistics and visualizations
- Integration with other Ergo ecosystem tools

## Donations

The Ergo ecosystem bounty program is supported by donations. Your contributions help:

- Fund Ergo core development
- Improve ecosystem tooling
- Promote Ergo technology among developers
- Increase bounty rewards

### Donation Wallets

You can donate to the Ergo Ecosystem Bounties program through the following wallets:

#### Multi-sig Wallet
`2BggBDgr9nBXyMpT5NbZf1QRN2pfHmzJxWwcfGEsgqzs94TEJv5GmtKTjmew74DjoTjTULa2A4RjJW6qGvniFm29KZKZ4attHxSZxuq1hQnXbURvoYm7jkHHzrd4ZF9u29cgHZczv2LWNiHoU6seFkC73JvGkT1khxkzRatPwDZ6aP87VPV6F4b1XmsitCB2DoKCYEtgtP1yCXmDhfSgdzDatn4SjSfZkxysggBH3TzJqTzZkqn8pp1DeAdiPJ1JZr8KeUGpnjkpjddoc`

#### Paideia Wallet
`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`

All donations are used to support the Ergo ecosystem bounty program and help grow the Ergo blockchain ecosystem.
