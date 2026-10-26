"""Client for executing GraphQL queries against DvO."""

import asyncio
import logging
import random
from collections.abc import Awaitable, Mapping, Sequence
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import aiohttp
from django.conf import settings
from tenacity import RetryCallState, retry, retry_if_exception, stop_after_attempt

logger = logging.getLogger(__name__)

MAX_RETRY_ATTEMPTS = 3
MIN_RETRY_DELAY = 2.0
MAX_RETRY_DELAY = 30.0
RETRY_AFTER_JITTER = 1.0
DEFAULT_MAX_CONCURRENT_REQUESTS = 2


class DvOResponseError(Exception):
    """Raised when DvO returns a response that cannot be used."""


async def _gather_all(*awaitables: Awaitable[Any]) -> list[Any]:
    results = await asyncio.gather(*awaitables, return_exceptions=True)
    values = []
    for result in results:
        if isinstance(result, BaseException):
            raise result
        values.append(result)
    return values


def _ensure_min_retry_delay(delay: float) -> float:
    """Ensure retries wait for at least the configured minimum delay."""
    return max(MIN_RETRY_DELAY, delay)


def _get_rate_limit_retry_delay(
    retry_after: str | None,
    attempt: int,
) -> float:
    """Return a jittered Retry-After delay or capped exponential backoff."""
    if retry_after is not None:
        try:
            delay = float(retry_after)
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(retry_after)
            except TypeError, ValueError, OverflowError:
                retry_at = None
            if retry_at is not None:
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=timezone.utc)
                delay = max(
                    (retry_at - datetime.now(timezone.utc)).total_seconds(),
                    0,
                )
                return _ensure_min_retry_delay(
                    delay + random.uniform(0, RETRY_AFTER_JITTER)
                )
        else:
            if delay >= 0:
                return _ensure_min_retry_delay(
                    delay + random.uniform(0, RETRY_AFTER_JITTER)
                )

    max_delay = min(
        MAX_RETRY_DELAY,
        MIN_RETRY_DELAY * (2 ** (attempt - 1)),
    )
    return _ensure_min_retry_delay(random.uniform(0, max_delay))


def _is_retryable_error(error: BaseException) -> bool:
    """Return whether an HTTP 429 or transient connection error can be retried."""
    is_rate_limited = (
        isinstance(error, aiohttp.ClientResponseError) and error.status == 429
    )
    is_connection_error = isinstance(
        error,
        (aiohttp.ClientConnectionError, asyncio.TimeoutError),
    )
    return is_rate_limited or is_connection_error


def _wait_for_retry(retry_state: RetryCallState) -> float:
    """Choose Retry-After for HTTP 429s or exponential backoff for other errors."""
    error = retry_state.outcome.exception() if retry_state.outcome is not None else None
    retry_after = (
        error.headers.get("Retry-After")
        if (
            isinstance(error, aiohttp.ClientResponseError)
            and error.status == 429
            and error.headers
        )
        else None
    )
    return _get_rate_limit_retry_delay(retry_after, retry_state.attempt_number)


def _log_retry(retry_state: RetryCallState) -> None:
    """Log each scheduled retry for a DvO request."""
    if retry_state.next_action is None or retry_state.outcome is None:
        return

    error = retry_state.outcome.exception()
    if isinstance(error, aiohttp.ClientResponseError):
        error_description = f"HTTP {error.status}"
    else:
        error_description = type(error).__name__
    logger.warning(
        f"DvO request failed with {error_description}; retrying in "
        f"{retry_state.next_action.sleep} seconds "
        f"(attempt {retry_state.attempt_number}/{MAX_RETRY_ATTEMPTS})"
    )


class DvOClient:
    """Execute generic DvO GraphQL queries within a shared async session."""

    def __init__(
        self,
        api_url: str | None = None,
        headers: Mapping[str, str] | None = None,
        max_concurrent_requests: int = DEFAULT_MAX_CONCURRENT_REQUESTS,
        timeout_total: float = 30.0,
    ) -> None:
        """Initialize the client using explicit options or DvO Django settings."""
        self.api_url = api_url if api_url is not None else settings.DVO_URL
        if headers is None:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
                "Authorization": aiohttp.encode_basic_auth(
                    settings.DVO_BASIC_AUTH_USERNAME,
                    settings.DVO_BASIC_AUTH_PASSWORD,
                ),
            }
        self.headers = dict(headers)
        if max_concurrent_requests < 1:
            raise ValueError("max_concurrent_requests must be at least 1")

        self.max_concurrent_requests = max_concurrent_requests
        self.timeout_total = timeout_total
        self._session: aiohttp.ClientSession | None = None
        self._semaphore: asyncio.Semaphore | None = None

    async def __aenter__(self) -> "DvOClient":
        """Open the shared HTTP session and initialize the request limit."""
        if self._session is not None:
            raise RuntimeError("DvoClient is already open")

        timeout = aiohttp.ClientTimeout(total=self.timeout_total)
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            headers=self.headers,
        )
        self._semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Close the HTTP session and release its request semaphore."""
        if self._session is not None:
            await self._session.close()
            self._session = None
            self._semaphore = None

    async def execute_query(
        self,
        query: str,
        variables: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Post a GraphQL query and return its data, logging any partial errors."""
        if self._session is None or self._semaphore is None:
            raise RuntimeError("DvOClient must be used as an async context manager")

        async with self._semaphore:
            logger.info(f"Executing DvO query with variables: {variables}")
            return await self._execute_query_with_retries(query, variables)

    @retry(
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=_wait_for_retry,
        retry=retry_if_exception(_is_retryable_error),
        before_sleep=_log_retry,
        reraise=True,
    )
    async def _execute_query_with_retries(
        self,
        query: str,
        variables: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a query with retries while its caller holds a concurrency slot."""
        if self._session is None:
            raise RuntimeError("DvOClient must be used as an async context manager")

        async with self._session.post(
            self.api_url,
            json={"query": query, "variables": dict(variables or {})},
        ) as response:
            response.raise_for_status()
            payload = await response.json()

        if not isinstance(payload, dict):
            raise DvOResponseError("DvO returned a non-object GraphQL response")

        errors = payload.get("errors")
        if errors:
            logger.warning(f"DvO GraphQL response contained errors: {errors}")

        data = payload.get("data")
        if not isinstance(data, dict):
            raise DvOResponseError("DvO GraphQL response did not contain usable data")
        return data

    async def execute_paginated_view_query(
        self,
        query: str,
        variables: Mapping[str, Any] | None = None,
        page_variable: str = "page",
    ) -> list[dict[str, Any]]:
        """Fetch every page of a view query and return the raw nodes in order."""
        query_variables = dict(variables or {})
        first_page = await self.execute_query(
            query,
            {**query_variables, page_variable: 1},
        )
        nodes, total_pages = self._get_view_nodes_and_page_count(first_page)

        remaining_pages = await _gather_all(
            *(
                self.execute_query(
                    query,
                    {**query_variables, page_variable: page},
                )
                for page in range(2, total_pages + 1)
            )
        )
        for page_data in remaining_pages:
            page_nodes, _ = self._get_view_nodes_and_page_count(page_data)
            nodes.extend(page_nodes)
        return nodes

    async def execute_paginated_view_queries(
        self,
        query: str,
        variable_sets: Sequence[Mapping[str, Any]],
        page_variable: str = "page",
    ) -> list[list[dict[str, Any]]]:
        """Fetch multiple paginated views concurrently, preserving input order."""
        return await _gather_all(
            *(
                self.execute_paginated_view_query(
                    query,
                    variables,
                    page_variable,
                )
                for variables in variable_sets
            )
        )

    @staticmethod
    def _get_view_nodes_and_page_count(
        data: Mapping[str, Any],
    ) -> tuple[list[dict[str, Any]], int]:
        """Extract nodes and total page count, raising if the view data is invalid."""
        view = data.get("view")
        if not isinstance(view, dict):
            raise DvOResponseError("DvO query response did not contain a view")

        nodes = view.get("nodes")
        if not isinstance(nodes, list) or any(
            not isinstance(node, dict) for node in nodes
        ):
            raise DvOResponseError("DvO view response did not contain usable nodes")

        pagination = view.get("pagination")
        if pagination is None:
            return nodes, 1
        if not isinstance(pagination, dict):
            raise DvOResponseError(
                "DvO view response contained invalid pagination data"
            )

        total_pages = pagination.get("totalPages")
        if (
            not isinstance(total_pages, int)
            or isinstance(total_pages, bool)
            or total_pages < 1
        ):
            raise DvOResponseError(
                "DvO view response contained an invalid totalPages value"
            )
        return nodes, total_pages
