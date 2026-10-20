import asyncio
import unittest
from unittest.mock import AsyncMock, patch

import aiohttp
from aioresponses import aioresponses
from django.test import override_settings

from core.testing_aioresponses import patch_client_response_init
from core.utils.dvo_utils import (
    DvOClient,
    DvOResponseError,
    _get_rate_limit_retry_delay,
)

patch_client_response_init()

API_URL = "https://dvo.example/graphql"


class DvOClientTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = DvOClient(api_url=API_URL, headers={})

    @override_settings(
        DVO_URL=API_URL,
        DVO_BASIC_AUTH_USERNAME="dvo-user",
        DVO_BASIC_AUTH_PASSWORD="dvo-password",
    )
    def test_client_uses_django_settings_for_endpoint_and_authentication(self):
        client = DvOClient()

        self.assertEqual(client.api_url, API_URL)
        self.assertEqual(
            client.headers["Authorization"],
            aiohttp.encode_basic_auth("dvo-user", "dvo-password"),
        )

    async def test_execute_query_returns_partial_data_and_logs_graphql_errors(self):
        response_data = {"view": {"nodes": [{"id": 1}]}}
        errors = [{"message": "A field could not be resolved"}]

        with aioresponses() as mocked:
            mocked.post(API_URL, payload={"data": response_data, "errors": errors})

            async with self.client:
                with self.assertLogs("core.utils.dvo_utils", level="WARNING") as logs:
                    result = await self.client.execute_query(
                        "query { view { nodes { id } } }"
                    )

        self.assertEqual(result, response_data)
        self.assertIn("response contained errors", logs.output[0])

    async def test_execute_query_raises_for_http_errors(self):
        with aioresponses() as mocked:
            mocked.post(API_URL, status=503)

            async with self.client:
                with self.assertRaises(aiohttp.ClientResponseError):
                    await self.client.execute_query("query { view { nodes { id } } }")

    async def test_execute_query_retries_rate_limit_using_retry_after_header(self):
        response_data = {"view": {"nodes": [{"id": 1}]}}
        query = "query { view { nodes { id } } }"
        with aioresponses() as mocked:
            mocked.post(API_URL, status=429, headers={"Retry-After": "0"})
            mocked.post(API_URL, payload={"data": response_data})

            async with self.client:
                with self.assertLogs("core.utils.dvo_utils", level="WARNING") as logs:
                    result = await self.client.execute_query(query)

        self.assertEqual(result, response_data)
        self.assertIn("retrying in 0.0 seconds", logs.output[0])
        self.assertEqual(sum(len(calls) for calls in mocked.requests.values()), 2)

    async def test_execute_query_stops_after_rate_limit_attempts_are_exhausted(self):
        with aioresponses() as mocked:
            mocked.post(
                API_URL,
                status=429,
                headers={"Retry-After": "0"},
                repeat=True,
            )

            async with self.client:
                with self.assertRaises(aiohttp.ClientResponseError):
                    await self.client.execute_query("query { view { nodes { id } } }")

        self.assertEqual(sum(len(calls) for calls in mocked.requests.values()), 3)

    async def test_execute_query_retries_server_disconnect(self):
        response_data = {"view": {"nodes": [{"id": 1}]}}
        query = "query { view { nodes { id } } }"
        with aioresponses() as mocked:
            mocked.post(API_URL, exception=aiohttp.ServerDisconnectedError())
            mocked.post(API_URL, payload={"data": response_data})

            with patch(
                "core.utils.dvo_utils.asyncio.sleep",
                new_callable=AsyncMock,
            ) as sleep:
                async with self.client:
                    with self.assertLogs(
                        "core.utils.dvo_utils",
                        level="WARNING",
                    ) as logs:
                        result = await self.client.execute_query(query)

        self.assertEqual(result, response_data)
        self.assertIn("ServerDisconnectedError", logs.output[0])
        sleep.assert_awaited_once_with(2.0)
        self.assertEqual(sum(len(calls) for calls in mocked.requests.values()), 2)

    def test_rate_limit_retry_delay_uses_exponential_fallback(self):
        self.assertEqual(_get_rate_limit_retry_delay(None, 1), 2)
        self.assertEqual(_get_rate_limit_retry_delay(None, 2), 4)

    def test_rate_limit_retry_delay_uses_retry_after_seconds(self):
        self.assertEqual(_get_rate_limit_retry_delay("1.5", 1), 1.5)

    async def test_execute_query_rejects_responses_without_data(self):
        with aioresponses() as mocked:
            mocked.post(API_URL, payload={"errors": [{"message": "Query failed"}]})

            async with self.client:
                with self.assertRaises(DvOResponseError):
                    await self.client.execute_query("query { view { nodes { id } } }")

    async def test_execute_paginated_view_query_fetches_every_page(self):
        requested_variables = []

        async def execute_query(query, variables=None):
            requested_variables.append(variables)
            page = variables["page"]
            return {
                "view": {
                    "nodes": [{"id": page}],
                    "pagination": {"totalPages": 3},
                }
            }

        self.client.execute_query = AsyncMock(side_effect=execute_query)

        nodes = await self.client.execute_paginated_view_query(
            "query($paragraphId: Int!, $page: Int!) { view { nodes { id } } }",
            {"paragraphId": 123},
        )

        self.assertEqual(nodes, [{"id": 1}, {"id": 2}, {"id": 3}])
        self.assertEqual(
            [variables["page"] for variables in requested_variables],
            [1, 2, 3],
        )
        self.assertTrue(
            all(variables["paragraphId"] == 123 for variables in requested_variables)
        )

    async def test_execute_paginated_view_queries_runs_queries_concurrently(self):
        query_barrier = asyncio.Barrier(
            2
        )  # Ensure both queries reach this point before proceeding to simulate concurrency

        async def execute_query(query, variables=None):
            await query_barrier.wait()
            return {
                "view": {
                    "nodes": [{"paragraphId": variables["paragraphId"]}],
                    "pagination": {"totalPages": 1},
                }
            }

        self.client.execute_query = AsyncMock(side_effect=execute_query)

        results = await asyncio.wait_for(
            self.client.execute_paginated_view_queries(
                "query($paragraphId: Int!, $page: Int!) { view { nodes { paragraphId } } }",
                [{"paragraphId": 123}, {"paragraphId": 456}],
            ),
            timeout=1,
        )

        self.assertEqual(
            results,
            [
                [{"paragraphId": 123}],
                [{"paragraphId": 456}],
            ],
        )

    async def test_execute_paginated_view_query_rejects_invalid_page_count(self):
        self.client.execute_query = AsyncMock(
            return_value={
                "view": {
                    "nodes": [],
                    "pagination": {"totalPages": None},
                }
            }
        )

        with self.assertRaises(DvOResponseError):
            await self.client.execute_paginated_view_query(
                "query { view { nodes { id } } }"
            )

    async def test_execute_paginated_view_queries_propagates_request_errors(self):
        self.client.execute_query = AsyncMock(
            side_effect=RuntimeError("DvO is unavailable")
        )

        with self.assertRaisesRegex(RuntimeError, "DvO is unavailable"):
            await self.client.execute_paginated_view_queries(
                "query($paragraphId: Int!, $page: Int!) { view { nodes { id } } }",
                [{"paragraphId": 123}, {"paragraphId": 456}],
            )
