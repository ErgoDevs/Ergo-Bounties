# Adding Missing Bounties to the Ergo Ecosystem

This guide provides instructions for adding bounties that aren't currently tracked in the Ergo Bounties system. By contributing missing bounties, you help ensure the Ergo ecosystem's bounty tracking remains comprehensive and up-to-date.

## Prerequisites

Before adding a missing bounty, ensure:

1. The bounty is not already listed in the [all bounties](/bounties/all.md) page
2. The bounty meets the criteria for inclusion (described below)

## Verifying Bounty Requirements

Before adding a new bounty, ensure it meets these criteria:
- It has a clear issue in a GitHub repository
- It has a specified bounty value
- It's tagged with "Bounty" or similar in the original repository

## Adding Repositories to Tracking

There are two ways to add repositories to our tracking system:

### 1. Add Individual Repositories

For adding specific repositories:

1. **Fork this repository**
2. **Edit the `tracked_repos.json` file** to add the new repository:
   ```json
   {"owner": "repo-owner", "repo": "repo-name"}
   ```
3. **Submit a PR** with title: `[ADD REPO] owner/repo-name`

### 2. Add Entire Organizations

For tracking all repositories within a GitHub organization:

1. **Fork this repository**
2. **Edit the `tracked_orgs.json` file** to add the organization:
   ```json
   {"org": "organization-name"}
   ```
3. **Submit a PR** with title: `[ADD ORG] organization-name`

When you add an organization, all non-archived repositories in that organization will be automatically tracked. This is particularly useful for organizations with many repositories containing bounties.

Once merged, the automated system will scan the repositories during the next update cycle and include any bounties it finds.

## For Manual Additions

There are two ways to manually add bounties that aren't in GitHub repositories:

### 1. Using the extra_bounties.json File

For direct addition of bounties without GitHub issues:

1. **Fork this repository**
2. **Edit the `bounties/extra_bounties.json` file** to add the new bounty:
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
3. **Submit a PR** with title: `[ADD MANUAL BOUNTY] Bounty Title`

The `extra_bounties.json` file allows you to directly add bounties that will be included in all listings alongside GitHub-sourced bounties.

### 2. Request Manual Addition

If you prefer not to edit the JSON file yourself:
- Create an issue in this repository
- Use title format: `[MANUAL BOUNTY] Brief description`
- Include: link to work, bounty value, and payment currency

> 💡 **Note:** The bounty listings are automatically updated daily via GitHub Actions. When you add a new repository to `tracked_repos.json` or a new organization to `tracked_orgs.json`, the system will automatically include their bounties in the next update.

## How the Automated System Works

Our automated bounty tracking system:
1. Scans all repositories listed in `tracked_repos.json` daily
2. Fetches all repositories from organizations listed in `tracked_orgs.json`
3. Identifies issues with bounty tags and extracts their details
4. Updates the bounty listings in various formats
5. Categorizes bounties by language and project

For more details on how the system works, see the [How It Works](/docs/how-it-works.md) guide.

## Questions or Support

If you have questions about adding missing bounties, please:

1. Open an issue in the Ergo-Bounties repository
2. Reach out on the Ergo Discord server
