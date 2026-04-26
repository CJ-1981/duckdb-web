"""
Batch Request Executor for Parallel API/HTML Scraping

Production-ready parallel HTTP request execution with:
- Multi-variable URL template substitution
- Token management with auto-refresh
- Network resilience and connectivity handling
- Intelligent retry with exponential backoff and circuit breaker
- Error aggregation and dead letter queue
- Rate limiting and concurrency control

@MX:NOTE: Enables large-scale web scraping (10k+ requests) with dynamic URL substitution
"""

import asyncio
import logging
import random
import re
import time
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for retry decisions"""
    TRANSIENT = "transient"      # Retryable: network blips, rate limits
    RECOVERABLE = "recoverable"   # Recoverable: token expiry, auth issues
    PERMANENT = "permanent"       # Not retryable: 404, 400, malformed requests
    CATASTROPHIC = "catastrophic" # System failure: no network, invalid config


class ErrorCategory(Enum):
    """Error categories for classification"""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server"
    CLIENT_ERROR = "client"
    TIMEOUT = "timeout"
    PARSING = "parsing"
    UNKNOWN = "unknown"


@dataclass
class HTTPError(Exception):
    """Structured error with context for intelligent handling"""
    status_code: Optional[int]
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    url: str
    retry_able: bool
    suggested_action: str
    original_exception: Optional[Exception] = None

    def __str__(self) -> str:
        return f"[{self.category.value}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization"""
        return {
            "status_code": self.status_code,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "url": self.url,
            "retry_able": self.retry_able,
            "suggested_action": self.suggested_action
        }


class TokenManager:
    """
    Manage authentication tokens with auto-refresh on expiry.

    @MX:NOTE: Handles bearer token refresh and OAuth2 rotation
    """

    def __init__(
        self,
        initial_token: str,
        refresh_token: Optional[str] = None,
        token_endpoint: Optional[str] = None,
        auth_type: str = "bearer",
        expires_in: Optional[int] = None,
        refresh_buffer: int = 60
    ):
        self.token = initial_token
        self.refresh_token = refresh_token
        self.token_endpoint = token_endpoint
        self.auth_type = auth_type
        self.expires_at = None
        self.refresh_lock = asyncio.Lock()

        if expires_in:
            self.expires_at = time.time() + expires_in - refresh_buffer

    async def get_valid_token(self) -> str:
        """Get current token, refreshing if expired"""
        async with self.refresh_lock:
            if self._is_expired():
                await self._refresh_token()
            return self.token

    def _is_expired(self) -> bool:
        """Check if token is expired or about to expire"""
        if not self.expires_at:
            return False
        return time.time() >= self.expires_at

    async def _refresh_token(self) -> None:
        """Refresh expired token"""
        if not self.refresh_token or not self.token_endpoint:
            raise ValueError("Cannot refresh token: no refresh_token or token_endpoint provided")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.token_endpoint,
                json={"refresh_token": self.refresh_token},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    raise HTTPError(
                        status_code=response.status,
                        category=ErrorCategory.AUTHENTICATION,
                        severity=ErrorSeverity.RECOVERABLE,
                        message="Token refresh failed",
                        url=self.token_endpoint,
                        retry_able=False,
                        suggested_action="Check refresh_token validity and token_endpoint URL"
                    )

                data = await response.json()
                self.token = data.get("access_token", self.token)

                if "expires_in" in data:
                    self.expires_at = time.time() + data["expires_in"] - 60

                logger.info(">>> [TOKEN MANAGER] Token refreshed successfully")

    def build_auth_headers(self) -> Dict[str, str]:
        """Build auth headers with current token"""
        if self.auth_type == "bearer":
            return {"Authorization": f"Bearer {self.token}"}
        elif self.auth_type == "api_key":
            return {"X-API-Key": self.token}
        else:
            return {}


class NetworkResilienceHandler:
    """
    Handle network connectivity issues with intelligent retry.

    @MX:NOTE: Classifies network errors and determines retry strategy
    """

    NETWORK_ERRORS = (
        aiohttp.ClientConnectorError,
        aiohttp.ClientOSError,
        aiohttp.ClientPayloadError,
        ConnectionRefusedError,
        asyncio.TimeoutError
    )

    @classmethod
    def classify_network_error(cls, error: Exception, url: str = "unknown") -> HTTPError:
        """Classify network error and determine retry strategy"""
        import socket
        error_msg = str(error).lower()

        # Connection refused
        if isinstance(error, ConnectionRefusedError):
            return HTTPError(
                status_code=None,
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.CATASTROPHIC,
                message=f"Connection refused: {error_msg}",
                url=url,
                retry_able=False,
                suggested_action="Server is not accepting connections",
                original_exception=error
            )

        # Timeout
        if isinstance(error, (asyncio.TimeoutError, TimeoutError)):
            return HTTPError(
                status_code=None,
                category=ErrorCategory.TIMEOUT,
                severity=ErrorSeverity.TRANSIENT,
                message=f"Request timeout: {error_msg}",
                url=url,
                retry_able=True,
                suggested_action="Request timed out - retry with longer timeout",
                original_exception=error
            )

        # Connection error
        if "connection" in error_msg or "network" in error_msg:
            return HTTPError(
                status_code=None,
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.TRANSIENT,
                message=f"Network connectivity issue: {error_msg}",
                url=url,
                retry_able=True,
                suggested_action="Transient network error - retry with exponential backoff",
                original_exception=error
            )

        # Default network error
        return HTTPError(
            status_code=None,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.TRANSIENT,
            message=f"Network error: {error_msg}",
            url=url,
            retry_able=True,
            suggested_action="Retry with exponential backoff",
            original_exception=error
        )

    @classmethod
    async def check_network_connectivity(cls, test_urls: Optional[List[str]] = None) -> bool:
        """Check if network connectivity is available"""
        if not test_urls:
            test_urls = [
                "https://www.google.com",
                "https://1.1.1.1",
                "https://api.github.com"
            ]

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for url in test_urls:
                try:
                    async with session.head(url) as response:
                        if response.status < 500:
                            return True
                except Exception:
                    continue

        return False


class RetryHandler:
    """
    Advanced retry logic with jitter, circuit breaking, and smart backoff.

    @MX:NOTE: Implements exponential backoff with jitter and circuit breaker pattern
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        jitter_range: float = 0.1,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: float = 60.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.jitter_range = jitter_range
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout

        # Circuit breaker state
        self.circuit_breaker_failures: Dict[str, int] = {}
        self.circuit_breaker_open_until: Dict[str, float] = {}

    def calculate_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff and jitter"""
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )

        if self.jitter:
            jitter_amount = delay * self.jitter_range
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)

    def should_retry(self, error: HTTPError, attempt: int) -> bool:
        """Determine if request should be retried"""
        if attempt >= self.max_retries:
            return False

        if self._is_circuit_open(error.url):
            return False

        return error.retry_able

    def _is_circuit_open(self, url: str) -> bool:
        """Check if circuit breaker is open for this URL"""
        if url in self.circuit_breaker_open_until:
            if time.time() < self.circuit_breaker_open_until[url]:
                return True
            else:
                # Circuit breaker timeout expired, reset
                del self.circuit_breaker_open_until[url]
                self.circuit_breaker_failures[url] = 0
        return False

    def _record_failure(self, url: str):
        """Record failure for circuit breaker"""
        self.circuit_breaker_failures[url] = self.circuit_breaker_failures.get(url, 0) + 1

        if self.circuit_breaker_failures[url] >= self.circuit_breaker_threshold:
            self.circuit_breaker_open_until[url] = time.time() + self.circuit_breaker_timeout
            logger.warning(f">>> [CIRCUIT BREAKER] Opened for {url} after {self.circuit_breaker_failures[url]} failures")

    def _record_success(self, url: str):
        """Record success, reset circuit breaker failure count"""
        if url in self.circuit_breaker_failures:
            self.circuit_breaker_failures[url] = 0


class ErrorAggregator:
    """
    Aggregate errors for batch operations and generate reports.

    @MX:NOTE: Tracks success/failure rates and manages dead letter queue
    """

    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.success_count = 0
        self.failure_count = 0
        self.dead_letter_queue: List[Dict[str, Any]] = []

    def record_success(self, url: str, row: Dict[str, Any]):
        """Record successful request"""
        self.success_count += 1

    def record_failure(self, url: str, row: Dict[str, Any], error: HTTPError, attempt: int):
        """Record failed request with full context"""
        self.failure_count += 1

        error_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "url": url,
            "input_data": row,
            "error": error.to_dict(),
            "attempt": attempt,
            "retry_able": error.retry_able
        }

        self.errors.append(error_record)

        # Add to dead letter queue if permanent failure
        if error.severity in [ErrorSeverity.PERMANENT, ErrorSeverity.CATASTROPHIC]:
            self.dead_letter_queue.append(error_record)

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive error report"""
        total = self.success_count + self.failure_count
        success_rate = (self.success_count / total * 100) if total > 0 else 0

        # Group errors by category
        errors_by_category = {}
        for error in self.errors:
            category = error["error"]["category"]
            errors_by_category[category] = errors_by_category.get(category, 0) + 1

        # Group errors by severity
        errors_by_severity = {}
        for error in self.errors:
            severity = error["error"]["severity"]
            errors_by_severity[severity] = errors_by_severity.get(severity, 0) + 1

        return {
            "summary": {
                "total_requests": total,
                "successful": self.success_count,
                "failed": self.failure_count,
                "success_rate": f"{success_rate:.2f}%"
            },
            "errors_by_category": errors_by_category,
            "errors_by_severity": errors_by_severity,
            "dead_letter_queue_size": len(self.dead_letter_queue),
            "retryable_failures": sum(1 for e in self.errors if e["retry_able"]),
            "permanent_failures": sum(1 for e in self.errors if not e["retry_able"])
        }

    def export_dead_letter_queue(self, filepath: str):
        """Export dead letter queue to JSON file for reprocessing"""
        with open(filepath, 'w') as f:
            json.dump(self.dead_letter_queue, f, indent=2)
        logger.info(f">>> [DEAD LETTER QUEUE] Exported {len(self.dead_letter_queue)} failed requests to {filepath}")

    def get_reprocessable_requests(self) -> List[Dict[str, Any]]:
        """Get retryable failed requests for reprocessing"""
        return [e for e in self.dead_letter_queue if e["retry_able"]]


class ParallelRequestExecutor:
    """
    Production-ready parallel request executor with comprehensive error handling.

    @MX:ANCHOR: Core batch processing engine for large-scale web scraping (fan_in: batch_request transform node)
    @MX:REASON: Single entry point ensures consistent error handling, retry logic, and performance optimization
    """

    def __init__(
        self,
        concurrency: int = 50,
        rate_limit: Optional[Dict[str, int]] = None,
        retry_policy: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        token_manager: Optional[TokenManager] = None
    ):
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.progress_callback = progress_callback
        self.token_manager = token_manager

        # Rate limiting (token bucket)
        self.rate_limit = rate_limit or {"requests_per_second": 100, "burst": 10}
        self.tokens = self.rate_limit["burst"]
        self.last_update = time.time()
        self.rate_lock = asyncio.Lock()

        # Retry handler
        self.retry_handler = RetryHandler(
            max_retries=retry_policy.get("max_retries", 3) if retry_policy else 3,
            base_delay=retry_policy.get("base_delay", 1.0) if retry_policy else 1.0,
            max_delay=retry_policy.get("max_delay", 60.0) if retry_policy else 60.0
        )

        # Error aggregator
        self.error_aggregator = ErrorAggregator()

    async def execute_batch(
        self,
        rows: List[Dict[str, Any]],
        url_template: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        extract_mode: str = "json",
        data_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute batch requests in parallel with comprehensive error handling.

        @MX:NOTE: Handles 10k+ requests with concurrency control and error aggregation
        """
        async with aiohttp.ClientSession() as session:
            tasks = []
            total = len(rows)

            # Create tasks for all requests
            for i, row in enumerate(rows):
                task = self._execute_single_request(
                    session,
                    row,
                    url_template,
                    method,
                    headers,
                    extract_mode,
                    data_path
                )
                tasks.append(task)

                # Progress update
                if self.progress_callback and i % 100 == 0:
                    progress = i / total
                    self.progress_callback(progress, f"Submitted {i}/{total} requests")

            # Execute all tasks concurrently
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            results = []
            for result in completed_results:
                if isinstance(result, Exception):
                    logger.error(f"Task failed: {result}")
                elif result:
                    results.append(result)

            # Generate error report
            error_report = self.error_aggregator.generate_report()
            logger.info(f">>> [BATCH COMPLETE] {error_report['summary']}")

            # Export dead letter queue if there are permanent failures
            if self.error_aggregator.dead_letter_queue:
                dlq_path = f"dead_letter_queue_{int(time.time())}.json"
                self.error_aggregator.export_dead_letter_queue(dlq_path)

            return results

    async def _execute_single_request(
        self,
        session: aiohttp.ClientSession,
        row: Dict[str, Any],
        url_template: str,
        method: str,
        headers: Optional[Dict[str, str]] = None,
        extract_mode: str = "json",
        data_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute single request with full error handling"""
        # Substitute URL template
        url = self._substitute_url(url_template, row)

        # Get fresh token if token manager is configured
        request_headers = headers.copy() if headers else {}
        if self.token_manager:
            token = await self.token_manager.get_valid_token()
            auth_headers = self.token_manager.build_auth_headers()
            request_headers.update(auth_headers)

        # Define request function with retry logic
        async def make_request():
            await self._acquire_token()

            async with self.semaphore:
                async with session.request(
                    method,
                    url,
                    headers=request_headers,
                    timeout=self.timeout
                ) as response:
                    response.raise_for_status()
                    return await self._get_response_data(response, extract_mode, data_path)

        # Execute with retry
        try:
            result = await self._execute_with_retry(make_request, url)

            # Record success
            self.error_aggregator.record_success(url, row)

            # Merge with input row - flatten dict results into top-level columns if possible
            if isinstance(result, dict):
                return {**row, **result}
            return {**row, "response": {"status": 200, "data": result}}

        except HTTPError as e:
            # Record failure
            self.error_aggregator.record_failure(url, row, e, attempt=0)

            # Return error result
            return {
                **row,
                "response": {
                    "status": e.status_code,
                    "error": e.message,
                    "category": e.category.value,
                    "retry_able": e.retry_able
                }
            }

        except Exception as e:
            # Unexpected error
            error = HTTPError(
                status_code=None,
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.CATASTROPHIC,
                message=str(e),
                url=url,
                retry_able=False,
                suggested_action="Check logs for details"
            )
            self.error_aggregator.record_failure(url, row, error, attempt=0)

            return {
                **row,
                "response": {
                    "status": None,
                    "error": str(e),
                    "category": "unknown"
                }
            }

    async def _execute_with_retry(self, func: Callable, url: str) -> Any:
        """Execute function with intelligent retry logic"""
        last_error = None

        for attempt in range(self.retry_handler.max_retries + 1):
            try:
                # Check circuit breaker before attempt
                if self.retry_handler._is_circuit_open(url):
                    raise HTTPError(
                        status_code=None,
                        category=ErrorCategory.NETWORK,
                        severity=ErrorSeverity.CATASTROPHIC,
                        message="Circuit breaker is open",
                        url=url,
                        retry_able=False,
                        suggested_action="Circuit breaker triggered - wait before retrying"
                    )

                # Execute request
                result = await func()

                # Record success
                self.retry_handler._record_success(url)

                return result

            except aiohttp.ClientResponseError as e:
                # Classify HTTP response error
                error = self._classify_http_response_error(e, url)
                last_error = error

                # Check if should retry
                if not self.retry_handler.should_retry(error, attempt):
                    self.retry_handler._record_failure(url)
                    raise error

                # Calculate delay and wait
                delay = self.retry_handler.calculate_delay(attempt)
                logger.warning(
                    f">>> [RETRY] Attempt {attempt + 1}/{self.retry_handler.max_retries} "
                    f"for {url} - {error.category.value} - "
                    f"retrying in {delay:.2f}s"
                )
                await asyncio.sleep(delay)

            except Exception as e:
                # Classify network error
                if isinstance(e, NetworkResilienceHandler.NETWORK_ERRORS):
                    error = NetworkResilienceHandler.classify_network_error(e, url)
                else:
                    error = HTTPError(
                        status_code=None,
                        category=ErrorCategory.UNKNOWN,
                        severity=ErrorSeverity.CATASTROPHIC,
                        message=f"Unknown error: {str(e)}",
                        url=url,
                        retry_able=False,
                        suggested_action="Check error details",
                        original_exception=e
                    )

                last_error = error

                # Check if should retry
                if not self.retry_handler.should_retry(error, attempt):
                    self.retry_handler._record_failure(url)
                    raise error

                # Calculate delay and wait
                delay = self.retry_handler.calculate_delay(attempt)
                logger.warning(
                    f">>> [RETRY] Attempt {attempt + 1}/{self.retry_handler.max_retries} "
                    f"for {url} - {error.category.value} - "
                    f"retrying in {delay:.2f}s"
                )
                await asyncio.sleep(delay)

        # All retries exhausted
        if last_error:
            raise last_error

    def _classify_http_response_error(self, error: aiohttp.ClientResponseError, url: str) -> HTTPError:
        """Classify HTTP response error"""
        status = error.status
        message = str(error)

        # 401 Unauthorized - token expired
        if status == 401:
            return HTTPError(
                status_code=status,
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.RECOVERABLE,
                message="Authentication failed - token may be expired",
                url=url,
                retry_able=True,
                suggested_action="Refresh authentication token",
                original_exception=error
            )

        # 403 Forbidden
        if status == 403:
            return HTTPError(
                status_code=status,
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.PERMANENT,
                message="Access forbidden - insufficient permissions",
                url=url,
                retry_able=False,
                suggested_action="Check API permissions and access rights",
                original_exception=error
            )

        # 404 Not Found
        if status == 404:
            return HTTPError(
                status_code=status,
                category=ErrorCategory.CLIENT_ERROR,
                severity=ErrorSeverity.PERMANENT,
                message="Resource not found",
                url=url,
                retry_able=False,
                suggested_action="Verify URL and resource existence",
                original_exception=error
            )

        # 429 Rate Limit
        if status == 429:
            return HTTPError(
                status_code=status,
                category=ErrorCategory.RATE_LIMIT,
                severity=ErrorSeverity.TRANSIENT,
                message="Rate limit exceeded",
                url=url,
                retry_able=True,
                suggested_action="Back off and retry with exponential delay",
                original_exception=error
            )

        # 5xx Server Errors
        if 500 <= status < 600:
            return HTTPError(
                status_code=status,
                category=ErrorCategory.SERVER_ERROR,
                severity=ErrorSeverity.TRANSIENT,
                message=f"Server error: {message}",
                url=url,
                retry_able=True,
                suggested_action="Retry with exponential backoff",
                original_exception=error
            )

        # Default client error
        return HTTPError(
            status_code=status,
            category=ErrorCategory.CLIENT_ERROR,
            severity=ErrorSeverity.PERMANENT,
            message=f"Client error: {message}",
            url=url,
            retry_able=False,
            suggested_action="Check request parameters",
            original_exception=error
        )

    def _substitute_url(self, template: str, row: Dict[str, Any]) -> str:
        """
        Substitute variables in URL template.

        Supports unlimited {variable} placeholders in path, query params, etc.

        @MX:NOTE: Multi-variable substitution using regex pattern matching
        """
        pattern = r'\{(\w+)\}'

        def replace(match):
            key = match.group(1)
            if key not in row:
                raise ValueError(f"Variable '{key}' not found in row data: {list(row.keys())}")
            return str(row[key])

        return re.sub(pattern, replace, template)

    async def _acquire_token(self):
        """Token bucket rate limiting algorithm"""
        async with self.rate_lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens += elapsed * self.rate_limit["requests_per_second"]
            self.tokens = min(self.tokens, self.rate_limit["burst"])
            self.last_update = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate_limit["requests_per_second"]
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1

    async def _get_response_data(
        self,
        response: aiohttp.ClientResponse,
        extract_mode: str = "json",
        data_path: Optional[str] = None
    ) -> Any:
        """Extract data from response based on extract_mode"""
        content_type = response.headers.get('Content-Type', '')

        if 'application/json' in content_type or extract_mode == "json":
            data = await response.json()

            # Apply JSONPath if specified
            if data_path:
                data = self._extract_jsonpath(data, data_path)

            return data

        elif 'text/html' in content_type or extract_mode == "html":
            return {"html": await response.text()}

        else:
            return {"text": await response.text()}

    def _extract_jsonpath(self, data: Any, path: str) -> Any:
        """
        Extract nested data using JSONPath notation.

        Supports: $.data.users[0].name
        """
        keys = path.replace('$.', '').split('.')
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit():
                index = int(key)
                value = value[index] if 0 <= index < len(value) else None
            else:
                return None

            if value is None:
                return None

        return value
