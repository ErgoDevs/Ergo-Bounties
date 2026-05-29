#!/usr/bin/env python3
"""
Base API Client Module

This module defines a base class for API clients, providing common
functionality such as session management, rate limiting, and error handling.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

# Configure logging
logger = logging.getLogger(__name__)

class BaseClient:
    """
    Base class for API clients.
    Handles session management, rate limiting, and error handling.
    """

    def __init__(self, base_url: str = "", timeout: int = 30, max_retries: int = 3, retry_delay: int = 5):
        """
        Initialize the API client.

        Args:
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay in seconds between retries
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    JsonResponse = Union[Dict[str, Any], List[Any]]

    def _make_json_request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[JsonResponse], Optional[Dict[str, Dict[str, str]]]]:
        """
        Make a request to the API with retry logic and rate limit handling.

        Args:
            url: API endpoint URL
            method: HTTP method (default: GET)
            headers: Optional headers to include in the request
            data: Optional data to send in the request body

        Returns:
            Tuple of (response JSON data, pagination links). Non-JSON responses are
            treated as invalid API responses instead of being passed downstream as text.
        """
        merged_headers = self.session.headers.copy()
        if headers:
            merged_headers.update(headers)

        for attempt in range(self.max_retries):
            try:
                full_url = url if url.startswith("http") else self.base_url + url
                response = self.session.request(
                    method=method,
                    url=full_url,
                    headers=merged_headers,
                    json=data,
                    timeout=self.timeout
                )

                # Check for rate limiting
                if response.status_code in (403, 429) and 'X-RateLimit-Remaining' in response.headers:
                    remaining = int(response.headers['X-RateLimit-Remaining'])
                    if remaining == 0:
                        reset_time = int(response.headers['X-RateLimit-Reset'])
                        sleep_time = max(1, reset_time - time.time())
                        logger.warning(f"Rate limit exceeded. Sleeping for {sleep_time} seconds")
                        time.sleep(sleep_time)
                        continue

                response.raise_for_status()
                try:
                    return response.json(), response.links
                except ValueError as exc:
                    logger.error("Expected JSON response from URL: %s", url)
                    raise requests.exceptions.RequestException(
                        f"Expected JSON response from URL: {url}"
                    ) from exc

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Max retries exceeded for URL: {url}")
                    raise requests.exceptions.RequestException(f"Max retries exceeded for URL: {url}")

        return None, None
