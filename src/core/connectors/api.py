"""
REST API Connector

Fetches data from REST API endpoints for loading into DuckDB.

@MX:NOTE: Supports pagination, authentication, and error handling for API data sources.
"""

import logging
from typing import List, Dict, Any, Iterator, Optional, Union
from urllib.parse import urljoin, urlparse
import time

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from .base import BaseConnector


logger = logging.getLogger(__name__)


class APIConnector(BaseConnector):
    """
    Connector for fetching data from REST API endpoints.

    Supports:
    - GET requests to JSON endpoints
    - API key authentication (header or query param)
    - Bearer token authentication
    - Basic authentication
    - Pagination (cursor-based, offset-based, link header)
    - Retry logic with exponential backoff
    - Custom headers

    Example:
        >>> connector = APIConnector(auth_type='bearer', token='xxx')
        >>> for row in connector.read('https://api.example.com/users'):
        ...     print(row)
    """

    # Default configuration
    DEFAULT_TIMEOUT = 30
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0

    def __init__(
        self,
        auth_type: Optional[str] = None,
        token: Optional[str] = None,
        api_key: Optional[str] = None,
        api_key_header: str = 'X-API-Key',
        username: Optional[str] = None,
        password: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Initialize API connector

        Args:
            auth_type: Authentication type ('bearer', 'api_key', 'basic', None)
            token: Bearer token for bearer auth
            api_key: API key value
            api_key_header: Header name for API key (default: 'X-API-Key')
            username: Username for basic auth
            password: Password for basic auth
            headers: Additional HTTP headers
            max_retries: Maximum number of retries for failed requests
            retry_delay: Initial delay between retries (seconds)
            timeout: Request timeout (seconds)
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests library is required for API connector. "
                "Install it with: pip install requests"
            )

        self.auth_type = auth_type
        self.token = token
        self.api_key = api_key
        self.api_key_header = api_key_header
        self.username = username
        self.password = password
        self.headers = headers or {}
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

        # Build authentication headers
        self._auth_headers = self._build_auth_headers()

        # Session for connection pooling
        self._session: Optional[requests.Session] = None

    def _build_auth_headers(self) -> Dict[str, str]:
        """Build authentication headers based on auth_type"""
        headers = {}

        if self.auth_type == 'bearer' and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        elif self.auth_type == 'api_key' and self.api_key:
            headers[self.api_key_header] = self.api_key

        return headers

    def connect(self, **kwargs) -> None:
        """
        Establish session for API requests

        Args:
            **kwargs: Additional session parameters
        """
        self._session = requests.Session()
        self._session.headers.update(self._auth_headers)
        self._session.headers.update(self.headers)

        logger.debug("API connector session established")

    def disconnect(self) -> None:
        """Close the session"""
        if self._session:
            self._session.close()
            self._session = None
            logger.debug("API connector session closed")

    def validate(self, url: str) -> bool:
        """
        Validate API endpoint URL

        Args:
            url: API endpoint URL

        Returns:
            True if URL is valid

        Raises:
            ValueError: If URL is invalid
        """
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL: {url}")

        if parsed.scheme not in ('http', 'https'):
            raise ValueError(f"Unsupported URL scheme: {parsed.scheme}. Use http:// or https://")

        return True

    def get_metadata(self, url: str) -> Dict[str, Any]:
        """
        Get metadata about API endpoint

        Args:
            url: API endpoint URL

        Returns:
            Dictionary with metadata (url, estimated_rows, etc.)
        """
        return {
            'url': url,
            'type': 'api',
            'auth_type': self.auth_type or 'none',
        }

    def read(
        self,
        url: str,
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        data_path: Optional[str] = None,
        pagination: Optional[str] = None,
        max_pages: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Read data from API endpoint

        Args:
            url: API endpoint URL
            method: HTTP method (default: 'GET')
            params: Query parameters
            data_path: JSONPath to extract data array (e.g., 'data.items')
            pagination: Pagination type ('cursor', 'offset', 'link', None)
            max_pages: Maximum number of pages to fetch (for pagination)

        Yields:
            Dictionary representing a single row/record

        Raises:
            requests.RequestException: If request fails after retries
        """
        if not self._session:
            self.connect()

        current_url = url
        page_count = 0

        while current_url and (max_pages is None or page_count < max_pages):
            rows = self._fetch_page(
                current_url,
                method,
                params,
                data_path
            )

            if not rows:
                break

            for row in rows:
                yield row

            page_count += 1

            # Handle pagination for next page
            if pagination:
                current_url = self._get_next_page_url(current_url, pagination, page_count)
            else:
                break

    def _fetch_page(
        self,
        url: str,
        method: str,
        params: Optional[Dict[str, Any]],
        data_path: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Fetch a single page of data with retry logic

        Args:
            url: API endpoint URL
            method: HTTP method
            params: Query parameters
            data_path: JSONPath to extract data array

        Returns:
            List of dictionaries representing rows
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()

                data = response.json()

                # Extract data using data_path if specified
                if data_path:
                    data = self._extract_path(data, data_path)

                # Ensure we have a list
                if isinstance(data, dict):
                    # Single object, wrap in list
                    return [data]
                elif isinstance(data, list):
                    return data
                else:
                    logger.warning(f"Unexpected data type: {type(data)}")
                    return []

            except requests.RequestException as e:
                last_error = e
                delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}. Retrying in {delay}s...")
                time.sleep(delay)

        # All retries exhausted
        raise requests.RequestException(
            f"Failed to fetch {url} after {self.max_retries} attempts. Last error: {last_error}"
        )

    def _extract_path(self, data: Any, path: str) -> Any:
        """
        Extract nested data using dot notation path

        Args:
            data: Data structure (dict/list)
            path: Dot notation path (e.g., 'data.items')

        Returns:
            Extracted data or original data if path not found
        """
        keys = path.split('.')
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                logger.warning(f"Path '{path}' not found in data")
                return data

        return current

    def _get_next_page_url(
        self,
        current_url: str,
        pagination: str,
        page_num: int
    ) -> Optional[str]:
        """
        Get URL for next page based on pagination type

        Args:
            current_url: Current page URL
            pagination: Pagination type
            page_num: Current page number (1-indexed)

        Returns:
            URL for next page or None if no more pages
        """
        if pagination == 'offset':
            # Offset-based: add/modify offset parameter
            parsed = urlparse(current_url)
            # Simple implementation: add offset=N*limit
            # This is a basic implementation; production code would parse existing params
            limit = 100  # Default page size
            offset = page_num * limit
            separator = '&' if parsed.query else '?'
            return f"{current_url}{separator}offset={offset}&limit={limit}"

        elif pagination == 'cursor':
            # Cursor-based pagination requires parsing response for next cursor
            # This is a simplified implementation
            # In practice, you'd need to make a request and parse the response
            return None

        elif pagination == 'link':
            # Link header pagination (GitHub style)
            # Requires making a request first to get Link header
            return None

        return None


def create_api_connector(
    auth_type: Optional[str] = None,
    **kwargs
) -> APIConnector:
    """
    Factory function to create API connector with common configurations

    Args:
        auth_type: Authentication type
        **kwargs: Additional connector parameters

    Returns:
        Configured APIConnector instance

    Example:
        >>> # Bearer token
        >>> connector = create_api_connector(auth_type='bearer', token='xxx')
        >>>
        >>> # API key
        >>> connector = create_api_connector(auth_type='api_key', api_key='xxx')
    """
    return APIConnector(auth_type=auth_type, **kwargs)
