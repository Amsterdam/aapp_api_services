"""Client for executing GraphQL queries against DvO."""

import asyncio
import logging
from collections.abc import Awaitable, Mapping, Sequence
from typing import Any

import aiohttp
from django.conf import settings

logger = logging.getLogger(__name__)


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


class DvOClient:
    """Execute generic DvO GraphQL queries within a shared async session."""

    def __init__(
        self,
        api_url: str | None = None,
        headers: Mapping[str, str] | None = None,
        max_concurrent_requests: int = 20,
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
            raise RuntimeError("DvoClient must be used as an async context manager")

        async with self._semaphore:
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
