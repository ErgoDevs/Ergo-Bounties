#!/usr/bin/env python3
"""
Bounty Processor Module

This module is the core of the bounty finder system. It:
- Processes GitHub repositories and organizations to find bounties
- Extracts and normalizes bounty information
- Organizes bounties by various criteria (language, organization, currency)
- Calculates statistics and aggregates data

The processor acts as a bridge between the data sources (GitHub API) and 
the generators that create the output markdown files.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional, Set

from ..api.github_client import GitHubClient
from ..api.currency_client import CurrencyClient
from .extractors import is_bounty_issue, extract_bounty_info

import json
import os # Added for os.listdir and os.path.isdir
import re # Added for regex in submission parsing
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger(__name__)

ACTIVE_SUBMISSION_STATUSES = {"in-progress", "awaiting-review", "reviewed"}
PLACEHOLDERS = {"", "YOUR_GITHUB_USERNAME", "YOUR_WALLET_ADDRESS", "YOUR_CONTACT_INFO", "YYYY-MM-DD"}


def _normalize_bounty_id(value: str) -> Optional[str]:
    """Normalize owner/repo#number bounty IDs and GitHub issue/PR URLs."""
    raw = str(value or "").strip()
    if not raw:
        return None

    parsed = urlparse(raw)
    if parsed.netloc.lower() == "github.com":
        match = re.fullmatch(r"/([^/]+)/([^/]+)/(?:issues|pull)/(\d+)", parsed.path)
        if match:
            owner, repo, number = match.groups()
            return f"{owner.lower()}/{repo.lower()}#{number}"

    match = re.fullmatch(r"([^/\s]+)/([^#\s]+)#(\d+)", raw)
    if match:
        owner, repo, number = match.groups()
        return f"{owner.lower()}/{repo.lower()}#{number}"
    return None


def _issue_bounty_id(owner: str, repo: str, issue_number: Any) -> str:
    return f"{owner.lower()}/{repo.lower()}#{issue_number}"


def _case_insensitive_key(mapping: Dict[str, Any], key: str) -> str:
    """Return the existing key matching key case-insensitively, or key."""
    lowered = key.lower()
    return next((existing for existing in mapping if existing.lower() == lowered), key)


class BountyProcessor:
    """
    Processor for bounty data.
    Handles fetching and processing bounty information from GitHub.
    """

    def __init__(self, github_token: str, rates: Dict[str, float]):
        """
        Initialize the bounty processor.

        Args:
            github_token: GitHub API token
            rates: Dictionary of currency conversion rates
        """
        self.github_client = GitHubClient(github_token)
        self.currency_client = CurrencyClient()
        self.currency_client.rates = rates  # Use provided rates
        self.bounty_data = []
        self.project_totals = {}
        self.reserved_count = 0
        self.reserved_bounty_ids = self._get_reserved_bounty_ids()

    def _get_reserved_bounty_ids(self) -> Set[str]:
        """
        Scans active submissions and returns normalized owner/repo#number IDs.
        """
        submission_path = "submissions"
        bounty_ids = set()
        if os.path.isdir(submission_path):
            logger.info(f"Scanning {submission_path} for reserved bounty IDs...")
            for filename in os.listdir(submission_path):
                if filename.endswith(".json"):
                    try:
                        with open(os.path.join(submission_path, filename), "r", encoding="utf-8") as f:
                            submission = json.load(f)
                    except (OSError, json.JSONDecodeError):
                        continue

                    status = str(submission.get("status", "")).strip().lower()
                    wallet = str(submission.get("wallet_address", "")).strip()
                    contributor = str(submission.get("contributor", "")).strip()
                    if (
                        status not in ACTIVE_SUBMISSION_STATUSES
                        or wallet in PLACEHOLDERS
                        or contributor in PLACEHOLDERS
                    ):
                        continue

                    bounty_id = _normalize_bounty_id(submission.get("bounty_id", ""))
                    if not bounty_id:
                        bounty_id = _normalize_bounty_id(submission.get("original_issue_link", ""))
                    if bounty_id:
                        bounty_ids.add(bounty_id)
            logger.info(f"Found {len(bounty_ids)} reserved bounty IDs.")
        else:
            logger.warning(f"Submissions directory not found: {submission_path}")
        return bounty_ids

    def process_repositories(self, repos_to_query: List[Dict[str, str]]) -> None:
        """
        Process repositories to find bounties.

        Args:
            repos_to_query: List of repository objects with 'owner' and 'repo' keys
        """
        for repo in repos_to_query:
            owner = repo['owner']
            repo_name = repo['repo']

            logger.info(f"Processing {owner}/{repo_name}...")

            # Get repository languages
            languages = self.github_client.get_repository_languages(owner, repo_name)
            primary_lang = languages[0] if languages else "Unknown"
            secondary_lang = languages[1] if len(languages) > 1 else "None"

            # Initialize project counter if not exists
            project_key = _case_insensitive_key(self.project_totals, owner)
            if project_key not in self.project_totals:
                self.project_totals[project_key] = {"count": 0, "value": 0.0}

            # Get issues
            issues = self.github_client.get_repository_issues(owner, repo_name)

            # Process each issue
            for issue in issues:
                self._process_issue(issue, owner, repo_name, primary_lang, secondary_lang)
        logger.info(f"Reserved bounties: {self.reserved_count}")

    def process_organizations(self, orgs_to_query: List[Dict[str, str]], repos_to_query: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Process organizations to find repositories.

        Args:
            orgs_to_query: List of organization objects with 'org' key
            repos_to_query: Current list of repositories

        Returns:
            Updated list of repositories
        """
        updated_repos = repos_to_query.copy()
        processed_repos = {f"{repo['owner']}/{repo['repo']}".lower() for repo in repos_to_query}

        for org_entry in orgs_to_query:
            org = org_entry['org']
            logger.info(f"Fetching repositories for organization: {org}")

            org_repos = self.github_client.get_organization_repos(org)
            for repo in org_repos:
                # Skip archived repositories
                if repo.get('archived', False):
                    logger.debug(f"Skipping archived repository: {org}/{repo['name']}")
                    continue

                # Skip forks if they don't have issues
                if repo.get('fork', False) and not repo.get('has_issues', False):
                    logger.debug(f"Skipping fork without issues: {org}/{repo['name']}")
                    continue

                # Add to repos_to_query if not already there
                repo_id = f"{org}/{repo['name']}"
                repo_key = repo_id.lower()
                if repo_key not in processed_repos:
                    logger.info(f"Adding repository from organization: {repo_id}")
                    repo_entry = {"owner": org, "repo": repo['name']}
                    updated_repos.append(repo_entry)
                    processed_repos.add(repo_key)

        return updated_repos

    def _process_issue(self, issue: Dict[str, Any], owner: str, repo_name: str, primary_lang: str, secondary_lang: str) -> None:
        """
        Process a single issue to check if it's a bounty.

        Args:
            issue: Issue object from GitHub API
            owner: Repository owner
            repo_name: Repository name
            primary_lang: Primary language of the repository
            secondary_lang: Secondary language of the repository
        """
        if issue['state'] == 'open':
            # Check against pre-scanned active submission IDs.
            bounty_id = _issue_bounty_id(owner, repo_name, issue["number"])
            if bounty_id in self.reserved_bounty_ids:
                 logger.debug(f"Issue {issue['html_url']} marked as Reserved due to submission file.")
                 issue['state'] = 'Reserved' # Mark as Reserved if submission exists
                 self.reserved_count += 1 # Increment counter

            title = issue['title']
            labels = issue['labels']

            # Check if this is a bounty issue
            if is_bounty_issue(title, labels):
                title = title.replace(",", " ")

                # Extract bounty information
                amount, currency = extract_bounty_info(issue)

                # Store the bounty information
                bounty_info = {
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    "owner": owner,
                    "repo": repo_name,
                    "title": title,
                    "url": issue['html_url'],
                    "amount": amount,
                    "currency": currency,
                    "primary_lang": primary_lang,
                    "secondary_lang": secondary_lang,
                    "labels": [label['name'] for label in labels],
                    "issue_number": issue['number'],
                    "creator": issue['user']['login'],  # GitHub username of the issue creator
                    "status": issue['state'],  # Add status
                    "created_at": issue.get("created_at", ""),
                    "updated_at": issue.get("updated_at", ""),
                    "comments": issue.get("comments", 0),
                    "assignees": [assignee.get("login", "") for assignee in issue.get("assignees", [])],
                }

                self.bounty_data.append(bounty_info)

                # Update project totals
                project_key = _case_insensitive_key(self.project_totals, owner)
                self.project_totals[project_key]["count"] += 1

                # Calculate ERG value for totals
                erg_value = self.currency_client.calculate_erg_value(amount, currency)
                self.project_totals[project_key]["value"] += erg_value

    def get_bounty_data(self) -> List[Dict[str, Any]]:
        """
        Get the processed bounty data.

        Returns:
            List of bounty information dictionaries
        """
        return self.bounty_data

    def get_project_totals(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the project totals.

        Returns:
            Dictionary of project totals
        """
        return self.project_totals

    def add_extra_bounties(self, extra_bounties: List[Dict[str, Any]]) -> None:
        """
        Add manually specified bounties from extra_bounties.json.

        Args:
            extra_bounties: List of bounty objects with all required fields
        """
        for bounty in extra_bounties:
            # Add the bounty to the bounty data
            self.bounty_data.append(bounty)

            # Update project totals
            owner = bounty["owner"]
            project_key = _case_insensitive_key(self.project_totals, owner)
            if project_key not in self.project_totals:
                self.project_totals[project_key] = {"count": 0, "value": 0.0}

            self.project_totals[project_key]["count"] += 1

            # Calculate ERG value for totals
            amount = bounty.get("amount", "Not specified")
            currency = bounty.get("currency", "Not specified")
            erg_value = self.currency_client.calculate_erg_value(amount, currency)
            self.project_totals[project_key]["value"] += erg_value

    def get_total_stats(self) -> Tuple[int, float]:
        """
        Get overall total statistics.

        Returns:
            Tuple of (total_bounties, total_value)
        """
        total_bounties = sum(project["count"] for project in self.project_totals.values())
        total_value = sum(project["value"] for project in self.project_totals.values())
        return total_bounties, total_value
