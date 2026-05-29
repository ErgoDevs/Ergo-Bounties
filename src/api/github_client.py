#!/usr/bin/env python3
"""
GitHub API Client Module

This module handles all interactions with the GitHub API, including fetching repositories,
issues, and language data. It implements rate limiting handling, error recovery, and
provides a clean interface for the rest of the application.

Primary interactions:
- Fetching organization repositories
- Fetching repository language information
- Fetching issues from repositories
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

from src.api.base_client import BaseClient

# Configure logging
logger = logging.getLogger(__name__)


class GitHubClient(BaseClient):
    """
    Client for interacting with the GitHub API.
    Handles authentication, rate limiting, and provides methods for common API operations.
    """

    def __init__(self, token: str, max_retries: int = 3, retry_delay: int = 5):
        """
        Initialize the GitHub API client.

        Args:
            token: GitHub API token for authentication
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay in seconds between retries
        """
        super().__init__(
            base_url="https://api.github.com",
            timeout=30,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        self.token = token
        self.session.headers.update({"Authorization": f"token {token}"})

    def _fetch_paginated_data(self, url: str, item_type: str = "items") -> List[Dict[str, Any]]:
        """
        Helper method to fetch data from paginated GitHub API endpoints.

        Args:
            url: The initial API endpoint URL.
            item_type: A descriptive name for the items being fetched (for logging).

        Returns:
            A list containing all items fetched across all pages.
        """
        all_items = []
        current_url: Optional[str] = url
        page_num = 1

        logger.debug(f"Fetching paginated {item_type} starting with URL: {current_url}")

        while current_url:
            data, links = self._make_json_request(current_url)
            if data is None: # Check for None explicitly, as empty list is valid
                logger.warning(f"Request failed or returned no data for {current_url}")
                break # Stop pagination if request fails

            # Ensure data is a list before extending
            if isinstance(data, list):
                all_items.extend(data)
                logger.debug(f"Page {page_num}: Fetched {len(data)} {item_type}, total: {len(all_items)}")
            else:
                 logger.error(f"Expected a list but got {type(data)} for {current_url}")
                 break # Stop if the data format is unexpected

            # Get the URL for the next page
            current_url = links.get("next", {}).get("url") if links else None
            page_num += 1

        logger.info(f"Finished fetching paginated {item_type}. Total items: {len(all_items)}")
        return all_items

    def get_organization_repos(self, org: str) -> List[Dict[str, Any]]:
        """
        Get all repositories for an organization.

        Args:
            org: Organization name

        Returns:
            List of repository objects
        """
        initial_url = f"/orgs/{org}/repos?per_page=100"
        return self._fetch_paginated_data(initial_url, item_type="repositories")

    def get_repository_languages(self, owner: str, repo: str) -> List[str]:
        """
        Get languages used in a repository, sorted by usage.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            List of languages (top 2 by usage)
        """
        url = f"/repos/{owner}/{repo}/languages"

        logger.debug(f"Fetching languages for repository: {owner}/{repo}")

        data, _ = self._make_json_request(url)
        if not data:
            return []
        if not isinstance(data, dict):
            logger.error("Expected language mapping but got %s for %s/%s", type(data), owner, repo)
            return []
        # Sort languages by bytes of code and get top 2 (or all if fewer than 2)
        sorted_languages = sorted(data.items(), key=lambda x: x[1], reverse=True)[:2]
        result = [lang[0] for lang in sorted_languages]

        logger.debug(f"Languages for {owner}/{repo}: {result}")
        return result

    def get_repository_issues(
        self, owner: str, repo: str, state: str = "open"
    ) -> List[Dict[str, Any]]:
        """
        Get issues from a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state (open, closed, all)

        Returns:
            List of issue objects
        """
        initial_url = f"/repos/{owner}/{repo}/issues?state={state}&per_page=100"
        return self._fetch_paginated_data(initial_url, item_type=f"{state} issues")
