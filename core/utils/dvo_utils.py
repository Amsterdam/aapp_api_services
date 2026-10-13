"""
Shared DvO GraphQL client utilities.

This module centralizes request handling for integrations that fetch data from
Drupal voor Overheid (DvO), including retries, partial GraphQL error handling,
and pagination support for queries that accept a ``$page`` variable.

Use:

    class NewsService(DvOClient):
        pass

    with NewsService() as client:
        result = client.execute(QUERY, {"id": "123"})
        print(result["data"], result["errors"])

        pages = client.fetch_all(
            PAGED_QUERY,
            get_pagination=lambda data: data["view"]["pagination"],
            get_nodes=lambda data: data["view"]["nodes"],
        )
        print(len(pages["nodes"]), pages["errors"])
"""

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Mapping, Sequence

import requests
from django.conf import settings
from tenacity import retry, retry_if_exception_type, stop_after_attempt

logger = logging.getLogger(__name__)


class DvOClientError(Exception):
    """BaseClass for all errors from this client."""


class DvOTransportError(DvOClientError):
    """Non-recoverable HTTP error (e.g., 400/401/403): retrying will not help."""


class DvOQueryError(DvOClientError):
    """GraphQL returned errors without usable data (or a fatal error)."""

    def __init__(self, errors: Sequence[Mapping[str, Any]]):
        self.errors = list(errors)
        messages = "; ".join(str(e.get("message")) for e in self.errors[:3])
        super().__init__(f"GraphQL errors: {messages}")


class DvORetryableError(DvOClientError):
    """Temporary error (network, 429/5xx, invalid JSON, transient GraphQL error).

    Retried by `make_request`; only raised if all attempts are exhausted.
    """

    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
        errors: Sequence[Mapping[str, Any]] | None = None,
    ):
        super().__init__(message)
        self.retry_after = retry_after
        self.errors = list(errors or [])


def _get_retry_wait_seconds(retry_state: Any) -> float:
    """Determine the number of seconds to wait before retrying based on the exception."""
    exception = retry_state.outcome.exception() if retry_state.outcome else None
    if isinstance(exception, DvORetryableError) and exception.retry_after is not None:
        return exception.retry_after
    return 2.0


class DvOClient:
    RETRY_STATUSES = [408, 425, 429, 500, 502, 503, 504]

    def __init__(
        self,
        *,
        timeout: float | tuple[float, float] = (5, 60),  # (connect, read)
        session: requests.Session | None = None,
    ):
        self.url = settings.DVO_URL
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        )
        self.session.auth = (
            settings.DVO_BASIC_AUTH_USERNAME,
            settings.DVO_BASIC_AUTH_PASSWORD,
        )

    def __enter__(self) -> "DvOClient":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def close(self) -> None:
        self.session.close()

    @staticmethod
    def _parse_retry_after(retry_after: str | None) -> float | None:
        """Parse a Retry-After header as seconds or an HTTP date."""
        if retry_after is None:
            return None

        try:
            return max(float(retry_after), 0.0)
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(retry_after)
            except TypeError, ValueError:
                return None

        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)

        return max((retry_at - datetime.now(timezone.utc)).total_seconds(), 0.0)

    def fetch_all(
        self,
        query: str,
        get_pagination: Callable[[dict[str, Any]], dict[str, Any]],
        get_nodes: Callable[[dict[str, Any]], list[Any] | None],
        variables: Mapping[str, Any] | None = None,
    ) -> dict:
        """
        Fetch all pages for a paginated GraphQL query.

        The query must accept a ``page`` variable because this method sets it on
        each request. For every successful page response, nodes are appended to
        the combined result and any partial GraphQL errors are collected.

        The response is a dictionary with the following shape:
        {
            "nodes": [...],
            "errors": [...],
            "pages": int,
        }

        Args:
            query (str): The GraphQL query to execute.
            get_pagination (Callable[[dict[str, Any]], dict[str, Any]]): Function to extract pagination info from the response.
            get_nodes (Callable[[dict[str, Any]], list[Any] | None]): Function to extract the nodes list from the response.
            variables (Mapping[str, Any] | None): Optional variables for the
                query. A local copy is used so the caller input is not mutated.

        Returns:
            dict: A dictionary containing combined nodes, collected errors, and
                the last fetched page number.

        """

        request_variables = dict(variables or {})

        result = {
            "nodes": [],
            "errors": [],
            "pages": 0,
        }

        max_pages = 10000
        page = 1

        for _ in range(1, max_pages + 1):
            request_variables["page"] = page
            page_result = self.execute(query, request_variables)

            try:
                page_info = get_pagination(page_result["data"])
            except KeyError, IndexError:
                page_info = None

            if not isinstance(page_info, dict):
                # Better to fail hard, than to miss pages
                raise DvOClientError(
                    "Failed to retrieve pagination info from the response."
                )
            result["pages"] = page
            result["nodes"].extend(get_nodes(page_result["data"]) or [])
            result["errors"].extend(page_result.get("errors") or [])
            if page_info.get("enabled") is False:
                break

            max_pages = page_info.get("totalPages", max_pages)
            next_page = page_info.get("nextPage")
            if not next_page:
                break

            if next_page <= page:
                raise DvOClientError(
                    "Next page number is not greater than the current page."
                )
            page = next_page

        return result

    def execute(
        self,
        query: str,
        variables: Mapping[str, Any] | None = None,
        operation_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute a single GraphQL query with retries.

        Returns a dictionary containing ``data`` and ``errors`` keys. Partial
        GraphQL errors, if any, are preserved in the ``errors`` list.

        Args:
            query (str): The GraphQL query to execute.
            variables (Mapping[str, Any] | None): Optional variables for the query.
            operation_name (str | None): Optional operation name for the query.

        Returns:
            dict[str, Any]: The result of the GraphQL query, containing "data" and "errors" keys.

        """
        payload = {"query": query}
        if variables:
            payload["variables"] = dict(variables)
        if operation_name:
            payload["operationName"] = operation_name
        return self.make_request(payload)

    @retry(
        stop=stop_after_attempt(5),
        wait=_get_retry_wait_seconds,
        retry=retry_if_exception_type(DvORetryableError),
        reraise=True,  # Reraise the GraphQLRetryableError after the last attempt
    )
    def make_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Make a POST request to the GraphQL server with the given payload.

        Args:
            payload (dict[str, Any]): The GraphQL request payload containing "query", "variables", and optionally "operationName".

        Returns:
            dict[str, Any]: The parsed response containing "data" and "errors" keys.

        Raises:
            DvORetryableError: If a retryable error occurs (network error,
                transient HTTP error, invalid JSON, or transient GraphQL
                error). When available, Retry-After is used to schedule the
                next retry.
            DvOTransportError: If a non-retryable HTTP error occurs.
        """
        try:
            response = self.session.post(self.url, json=payload, timeout=self.timeout)
            response.raise_for_status()  # Raises an HTTPError for an unsuccessful status code
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            logger.error(f"GraphQL request failed with HTTP {status}: {e}")
            logger.info(
                "Request metadata: url=%s operation_name=%s variables=%s",
                e.request.url,
                payload.get("operationName"),
                payload.get("variables"),
            )
            if status in self.RETRY_STATUSES:
                raise DvORetryableError(
                    f"HTTP {status}",
                    retry_after=self._parse_retry_after(
                        e.response.headers.get("Retry-After")
                    ),
                ) from e
            raise DvOTransportError(f"HTTP {status}: {e.response.text[:500]}") from e
        except requests.exceptions.RequestException as e:  # connection, timeout, ...
            logger.error(f"GraphQL request failed: {e}")
            raise DvORetryableError(f"Network error: {e}") from e
        return self._parse_response(response)

    def _parse_response(self, response: requests.Response) -> dict[str, Any]:
        """
        Parse the GraphQL response.

        Args:
            response (requests.Response): The HTTP response from the GraphQL server.

        Returns:
            dict[str, Any]: The parsed response containing "data" and "errors"
                keys. Partial GraphQL errors are returned alongside the data.
        """
        try:
            body = response.json()
        except ValueError as e:
            logger.error("GraphQL response is not valid JSON")
            raise DvORetryableError("Response is not valid JSON") from e

        data = body.get("data")
        errors: list[dict[str, Any]] = body.get("errors") or []

        if data is None:
            if not errors:
                logger.error("GraphQL response contains no data and no errors")
                raise DvORetryableError("Response contains no data and no errors")
            if self._is_transient(errors):
                logger.error(f"GraphQL returned only errors: {errors[:3]}")
                raise DvORetryableError(
                    f"GraphQL errors: {errors[0].get('message')}", errors=errors
                )
            raise DvOQueryError(errors)

        if errors:
            for e in errors:
                logger.warning(
                    "GraphQL partial error: %s (path=%s)",
                    e.get("message"),
                    ".".join(map(str, e.get("path") or [])),
                )
        return {"data": data, "errors": errors}
