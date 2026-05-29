# 🤖 Ergo Bounties: How It Works

This document explains the technical details of how the Ergo Ecosystem Bounties repository automatically tracks, updates, and displays bounties across the Ergo blockchain ecosystem.

## Automated Bounty Tracking System

The repository uses GitHub Actions to automatically track and update the list of open bounties from various projects in the Ergo ecosystem.

### Automation Schedule

- **Daily Updates**: The bounty list is refreshed every day at midnight UTC
- **Submission PR Triage**: Submission PRs are triaged when opened/updated and again daily at 09:00 UTC
- **Ops Status**: A weekly ops issue is updated every Monday at 09:30 UTC
- **Manual Trigger**: Maintainers can manually run the workflow when needed

### How It Works

The automation process follows these steps:

1. **Repository Scanning**: The system scans repositories listed in `src/config/tracked_repos.json` and non-archived repositories from `src/config/tracked_orgs.json`
2. **Issue Identification**: It identifies issues with bounty tags or mentions in their title or description
3. **Bounty Extraction**: The system extracts bounty amounts and currencies using pattern matching
4. **Value Calculation**: Where possible, it converts different currencies to ERG equivalent values
5. **Reservation Filtering**: It hides bounties already claimed by open `submissions/*.json` PRs
6. **Report Generation**: It generates updated bounty reports in various formats and categories
7. **Validation and Commit**: Generated output is validated, then committed only when files changed

## Adding Repositories to Tracking

To add a new repository to the tracking system:

1. Fork this repository
2. Edit the `src/config/tracked_repos.json` file to add the new repository
   ```json
   {"owner": "repo-owner", "repo": "repo-name"}
   ```
3. Submit a PR with title: `[ADD REPO] owner/repo-name`

Once merged, the automation will include the new repository's bounties in the next update.

## Source of Truth

The repository separates editable source inputs from generated outputs.

Editable source inputs:

- `src/config/tracked_repos.json`: individual repositories to scan
- `src/config/tracked_orgs.json`: organizations whose non-archived repositories are scanned
- `src/config/extra_bounties.json`: manually maintained bounties and ongoing programs
- `submissions/*.json`: contributor reservations, review states, and payment records
- `src/**`: generator, API, extraction, validation, and formatting code
- `docs/**`: maintainer and contributor documentation

Generated outputs:

- `data/all.md`, `data/summary.md`, `data/featured_bounties.md`, `data/high-value-bounties.md`
- `data/new-bounties.md`, `data/recently-active.md`, `data/stale-bounties.md`, `data/starter-bounties.md`
- `data/by_language/*.md`, `data/by_currency/*.md`, `data/by_org/*.md`
- `submissions/payment_status.md`, `submissions/payment_queue.md`, `submissions/paid.md`, `submissions/triage.md`
- README badges and latest-update marker

Do not patch generated totals or category pages directly. Update the source config or generator code, run the generator, and commit the regenerated output.

## Adding Manual Bounties and Grants

For bounties that aren't in GitHub repositories or don't follow standard formats:

1. Fork this repository
2. Edit the `src/config/extra_bounties.json` file to add the new bounty:
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
     "creator": "your-username",
     "description": "Brief description of the bounty",
     "status": "Open"
   }
   ```
3. Submit a PR with title: `[ADD MANUAL BOUNTY] Bounty Title`

The `status` field can be set to:
- `"Open"`: The bounty is available for claiming (displays a "Reserve" button)
- `"In Progress"`: Someone is already working on the bounty (displays "In Progress" instead of the "Reserve" button)

Manual bounties added to `extra_bounties.json` will appear in the "Grants and Additional Bounties" section of the ongoing-programs.md file, separate from the automatically discovered GitHub issues which appear in their own dedicated pages.

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

## Submission Automation

Submissions and reservations use JSON files in `submissions/`.

- `status: in-progress` reserves a bounty.
- `status: awaiting-review` means upstream work is ready for reviewer check.
- `status: reviewed` means payment can be prepared.
- `status: paid` means payment details are complete.

The main automation is `.github/workflows/triage-submission-prs.yml`, backed by `scripts/triage_submission_prs.py`.
It checks JSON validity, required fields, contributor/PR author match, placeholder wallet values, duplicate bounty claims, stale reservations, and linked upstream PR merge state. It labels PRs, comments with findings, requests/tag reviewers, closes clearly invalid submission PRs, and writes `submissions/triage.md` during scheduled runs.

Payment reports are generated by `src/generators/payment_status_generator.py`:

- `submissions/payment_status.md`: active claims and reservations
- `submissions/payment_queue.md`: reviewed claims awaiting payment
- `submissions/paid.md`: paid claims

The weekly ops workflow (`.github/workflows/ops-status.yml`) updates a GitHub issue with open submission health, stale/invalid counts, payment queue count, and data freshness.

## Technical Implementation

The bounty tracking is implemented in Python using the GitHub API. The main components are:

- **GitHub Actions Workflow**: Defined in `.github/workflows/update-bounties.yml`
- **Python Script**: Located at `src/bounty_finder.py`
- **Repository List**: Maintained in `src/config/tracked_repos.json`

### GitHub API Usage

The script uses the GitHub API to:
- Fetch repository language information
- Retrieve open issues from tracked repositories
- Extract issue details including labels, title, and body

### Output Files

The system generates:
- `data/all.md`: formatted table of all open bounties
- `data/new-bounties.md`: newest created bounties
- `data/recently-active.md`: most recently updated bounties
- `data/stale-bounties.md`: old bounties with little recent activity
- `data/starter-bounties.md`: smaller, easier-to-start bounties
- Language-specific Markdown files in the `data/by_language/` directory
- Currency-specific Markdown files in the `data/by_currency/` directory
- Organization-specific Markdown files in the `data/by_org/` directory
- Summary statistics including total counts and values

## For Developers

This section provides information for developers who want to contribute to the Ergo Bounties codebase.

### Code Organization

The repository code is structured as follows:

```
.
├── src/                  # Source code
│   ├── api/              # API clients (GitHub, Currency)
│   ├── config/           # Configuration files
│   │   ├── constants.json    # Application constants
│   │   ├── extra_bounties.json    # Manually added bounties
│   │   ├── tracked_orgs.json      # Organizations to track
│   │   └── tracked_repos.json     # Repositories to track
│   ├── core/             # Core application logic
│   ├── generators/       # Markdown file generators
│   ├── tests/            # Test scripts
│   │   ├── github_actions_check.py  # CI/CD validation
│   │   ├── run_bounty_check.py      # Data validation
│   │   └── test_runner.py           # Test framework
│   ├── utils/            # Utility functions
│   └── bounty_finder.py  # Main application entry point
├── data/                 # Generated data files
│   ├── by_currency/      # Bounties grouped by currency
│   ├── by_language/      # Bounties grouped by programming language
│   ├── by_org/           # Bounties grouped by organization
│   └── *.md              # Summary and index files
├── docs/                 # Documentation
├── submissions/          # Bounty submissions from users
└── test.sh               # Test runner script
```

### Key Components for Developers

#### 1. Main Generator (`src/generators/main.py`)

This module writes the generated Markdown pages and README badges.

#### 2. Configuration System

Two main configuration files control the system behavior:

##### `src/config/constants.json`
Contains project-wide constants like:
```json
{
  "language_colors": {
    "Scala": "DC322F",
    "Rust": "DEA584"
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

```bash
python3 -m src.bounty_finder
python3 -m src.tests.run_bounty_check
python3 -m src.generators.payment_status_generator
python3 -m pytest -q src/tests
python3 -m py_compile run.py src/bounty_finder.py scripts/triage_submission_prs.py scripts/update_ops_issue.py
git diff --check
```

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

For donation wallet addresses and more information, please see the [donation page](/docs/donate.md).

All donations are used to support the Ergo ecosystem bounty program and help grow the Ergo blockchain ecosystem.
