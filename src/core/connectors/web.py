"""
Web Scraper Connector

Scrapes tabular data from web pages using HTML parsing.
"""

import logging
import re
from typing import List, Dict, Any, Iterator, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from .base import BaseConnector

logger = logging.getLogger(__name__)


class WebConnector(BaseConnector):
    """
    Connector for scraping tabular data from web pages.

    Supports:
    - HTML table extraction (finds <table> elements)
    - CSS selector-based extraction
    - XPath-based extraction (via lxml)
    - Custom headers for authentication
    - Automatic header row detection

    Example:
        >>> connector = WebConnector()
        >>> for row in connector.read('https://example.com/data', selector='table'):
        ...     print(row)
    """

    DEFAULT_TIMEOUT = 30

    def __init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        if not REQUESTS_AVAILABLE:
            raise ImportError(
                "requests library is required for Web connector. "
                "Install it with: pip install requests"
            )
        self.headers = headers or {}
        self.timeout = timeout
        self._session: Optional[requests.Session] = None

    def connect(self, **kwargs) -> None:
        self._session = requests.Session()
        self._session.headers.update(self.headers)
        if 'User-Agent' not in self._session.headers:
            self._session.headers['User-Agent'] = (
                'Mozilla/5.0 (compatible; DuckDBDataProcessor/1.0)'
            )

    def disconnect(self) -> None:
        if self._session:
            self._session.close()
            self._session = None

    def validate(self, url: str) -> bool:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL: {url}")
        if parsed.scheme not in ('http', 'https'):
            raise ValueError(f"Unsupported scheme: {parsed.scheme}")
        return True

    def get_metadata(self, url: str) -> Dict[str, Any]:
        return {'url': url, 'type': 'web'}

    def read(
        self,
        url: str,
        selector: str = 'table',
        extract_mode: str = 'table',
        **kwargs,
    ) -> Iterator[Dict[str, Any]]:
        """
        Scrape data from a web page.

        Args:
            url: Page URL to scrape
            selector: CSS selector or XPath expression
            extract_mode: 'table', 'css', or 'xpath'
        """
        if not self._session:
            self.connect()

        self.validate(url)

        response = self._session.get(url, timeout=self.timeout)
        response.raise_for_status()
        html = response.text

        if extract_mode == 'table':
            yield from self._extract_tables(html, selector)
        elif extract_mode == 'css':
            yield from self._extract_css(html, selector)
        elif extract_mode == 'xpath':
            yield from self._extract_xpath(html, selector)
        else:
            raise ValueError(f"Unknown extract_mode: {extract_mode}. Use 'table', 'css', or 'xpath'.")

    def _extract_tables(self, html: str, selector: str) -> Iterator[Dict[str, Any]]:
        """Extract data from HTML tables."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'lxml')
        tables = soup.select(selector)

        for table in tables:
            rows = table.find_all('tr')
            if not rows:
                continue

            # Detect header row
            header_cells = rows[0].find_all(['th', 'td'])
            headers = [self._clean_text(cell.get_text()) for cell in header_cells]

            # If first row looks like data (no <th>), use generic column names
            has_th = any(cell.name == 'th' for cell in header_cells)
            if not has_th:
                headers = [f'col_{i}' for i in range(len(header_cells))]
                data_rows = rows
            else:
                data_rows = rows[1:]

            for row in data_rows:
                cells = row.find_all(['td', 'th'])
                if not cells:
                    continue
                values = [self._clean_text(cell.get_text()) for cell in cells]
                row_dict = {}
                for i, val in enumerate(values):
                    key = headers[i] if i < len(headers) else f'col_{i}'
                    row_dict[key] = val if val else None
                if any(v is not None for v in row_dict.values()):
                    yield row_dict

    def _extract_css(self, html: str, selector: str) -> Iterator[Dict[str, Any]]:
        """Extract data using CSS selector - each matched element becomes a row."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'lxml')
        elements = soup.select(selector)

        for el in elements:
            row = {}
            # If element has children, extract text from each direct child
            children = list(el.children)
            text_children = [c for c in children if hasattr(c, 'get_text') or isinstance(c, str)]

            if len(text_children) > 1:
                for i, child in enumerate(text_children):
                    val = self._clean_text(child.get_text()) if hasattr(child, 'get_text') else str(child).strip()
                    row[f'col_{i}'] = val if val else None
            else:
                text = self._clean_text(el.get_text())
                if text:
                    row['value'] = text

            if row:
                yield row

    def _extract_xpath(self, html: str, xpath: str) -> Iterator[Dict[str, Any]]:
        """Extract data using XPath expression."""
        from lxml import etree

        tree = etree.HTML(html)
        elements = tree.xpath(xpath)

        for el in elements:
            if isinstance(el, str):
                text = el.strip()
                if text:
                    yield {'value': text}
            elif hasattr(el, 'text_content'):
                text = self._clean_text(el.text_content())
                if text:
                    yield {'value': text}

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text: normalize whitespace, strip."""
        return re.sub(r'\s+', ' ', text).strip()
