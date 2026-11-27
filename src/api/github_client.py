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
import re
import urllib.parse
from typing import List, Dict, Any, Optional, Tuple

import requests

from src.api.base_client import BaseClient

# Configure logging
logger = logging.getLogger(__name__)


def _pr_references_issue(pr: Dict[str, Any], owner: str, repo: str, issue_number: int) -> bool:
    """
    Check whether a merged PR genuinely references ``owner/repo#issue_number``.

    Handles common Ergo repository conventions:
    - ``#1884`` or ``Closes #1884`` in title/body (ignoring ``other/repo#1884``)
    - ``owner/repo#1884`` or ``https://github.com/owner/repo/issues/1884`` in title/body
    - ``1753 - ...``, ``1588 ...``, ``i1885``, ``I1868`` in the PR title
    """
    if pr.get("number") == issue_number:
        return False

    num = re.escape(str(issue_number))
    repo_slug = f"{re.escape(owner)}/{re.escape(repo)}"
    title = str(pr.get("title") or "")
    body = str(pr.get("body") or "")
    combined = f"{title}\n{body}"

    # Explicit repo-qualified reference or full GitHub issue URL
    qualified_re = re.compile(
        rf"(?:https?://github\.com/{repo_slug}/issues/{num}|(?<![A-Za-z0-9_.-]){repo_slug}#{num})(?!\d)",
        re.IGNORECASE,
    )
    if qualified_re.search(combined):
        return True

    # Unqualified #1234 (must not be preceded by owner/repo, word char, or slash)
    unqualified_hash_re = re.compile(rf"(?<![A-Za-z0-9_/.-])#{num}(?!\d)")
    if unqualified_hash_re.search(combined):
        return True

    # Title-only shorthand common in Ergo repos: "1753 - ...", "i1885 ...", "I1868 ..."
    title_shorthand_re = re.compile(rf"(?<![A-Za-z0-9_#/.-])[iI]?{num}(?!\d)")
    if title_shorthand_re.search(title):
        return True

    return False


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

    def search_merged_prs_for_issues(
        self, owner: str, repo: str, issue_numbers: List[int]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Search merged pull requests in ``owner/repo`` that reference any of ``issue_numbers``.

        Batches up to 6 issue numbers per GitHub Search API query (at most 5 ``OR`` operators,
        within GitHub's search syntax limit) and post-filters results with boundary-aware matching
        so open bounties with already-merged work can be surfaced as ``possibly-resolved``.
        """
        valid_numbers = sorted({int(n) for n in issue_numbers if isinstance(n, int) and n > 0})
        if not valid_numbers:
            return {}

        matches: Dict[int, Dict[int, Dict[str, Any]]] = {}
        batch_size = 6  # <= 5 OR operators per GitHub Search API query

        for idx in range(0, len(valid_numbers), batch_size):
            batch = valid_numbers[idx : idx + batch_size]
            terms = " OR ".join(str(n) for n in batch)
            query = f"repo:{owner}/{repo} is:pr is:merged ({terms})" if len(batch) > 1 else f"repo:{owner}/{repo} is:pr is:merged {terms}"
            url = f"/search/issues?per_page=100&q={urllib.parse.quote(query)}"

            try:
                data, _ = self._make_json_request(url)
            except requests.exceptions.RequestException as exc:
                logger.warning("Merged PR search failed for %s/%s (%s): %s", owner, repo, batch, exc)
                continue

            if not isinstance(data, dict):
                continue

            items = data.get("items")
            if not isinstance(items, list):
                continue

            for item in items:
                pr_number = item.get("number")
                pr_url = item.get("html_url")
                if not isinstance(pr_number, int) or not pr_url:
                    continue
                for issue_num in batch:
                    if _pr_references_issue(item, owner, repo, issue_num):
                        matches.setdefault(issue_num, {})[pr_number] = {
                            "number": pr_number,
                            "title": str(item.get("title") or ""),
                            "url": str(pr_url),
                        }

        return {
            issue_num: [prs_by_num[k] for k in sorted(prs_by_num)]
            for issue_num, prs_by_num in matches.items()
        }
