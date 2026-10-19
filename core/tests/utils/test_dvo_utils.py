import asyncio
import logging
from unittest.mock import AsyncMock

import aiohttp
import pytest
from aioresponses import aioresponses
from django.test import override_settings

from core.testing_aioresponses import patch_client_response_init
from core.utils.dvo_utils import DvOClient, DvOResponseError

patch_client_response_init()

API_URL = "https://dvo.example/graphql"


@override_settings(
    DVO_URL=API_URL,
    DVO_BASIC_AUTH_USERNAME="dvo-user",
    DVO_BASIC_AUTH_PASSWORD="dvo-password",
)
def test_client_uses_django_settings_for_endpoint_and_authentication():
    client = DvOClient()

    assert client.api_url == API_URL
    assert client.headers["Authorization"] == aiohttp.encode_basic_auth(
        "dvo-user",
        "dvo-password",
    )


@pytest.mark.asyncio
async def test_execute_query_returns_partial_data_and_logs_graphql_errors(caplog):
    response_data = {"view": {"nodes": [{"id": 1}]}}
    errors = [{"message": "A field could not be resolved"}]

    with aioresponses() as mocked:
        mocked.post(API_URL, payload={"data": response_data, "errors": errors})

        with caplog.at_level(logging.WARNING, logger="core.utils.dvo_utils"):
            async with DvOClient(api_url=API_URL, headers={}) as client:
                result = await client.execute_query("query { view { nodes { id } } }")

    assert result == response_data
    assert "response contained errors" in caplog.text


@pytest.mark.asyncio
async def test_execute_query_raises_for_http_errors():
    with aioresponses() as mocked:
        mocked.post(API_URL, status=503)

        async with DvOClient(api_url=API_URL, headers={}) as client:
            with pytest.raises(aiohttp.ClientResponseError):
                await client.execute_query("query { view { nodes { id } } }")


@pytest.mark.asyncio
async def test_execute_query_rejects_responses_without_data():
    with aioresponses() as mocked:
        mocked.post(API_URL, payload={"errors": [{"message": "Query failed"}]})

        async with DvOClient(api_url=API_URL, headers={}) as client:
            with pytest.raises(DvOResponseError):
                await client.execute_query("query { view { nodes { id } } }")


@pytest.mark.asyncio
async def test_execute_paginated_view_query_fetches_every_page():
    client = DvOClient(api_url=API_URL, headers={})
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

    client.execute_query = AsyncMock(side_effect=execute_query)

    nodes = await client.execute_paginated_view_query(
        "query($paragraphId: Int!, $page: Int!) { view { nodes { id } } }",
        {"paragraphId": 123},
    )

    assert nodes == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert [variables["page"] for variables in requested_variables] == [1, 2, 3]
    assert all(variables["paragraphId"] == 123 for variables in requested_variables)


@pytest.mark.asyncio
async def test_execute_paginated_view_queries_runs_queries_concurrently():
    client = DvOClient(api_url=API_URL, headers={})
    active_queries = 0
    maximum_active_queries = 0

    async def execute_query(query, variables=None):
        nonlocal active_queries, maximum_active_queries
        active_queries += 1
        maximum_active_queries = max(maximum_active_queries, active_queries)
        await asyncio.sleep(0.01)
        active_queries -= 1
        return {
            "view": {
                "nodes": [{"paragraphId": variables["paragraphId"]}],
                "pagination": {"totalPages": 1},
            }
        }

    client.execute_query = AsyncMock(side_effect=execute_query)

    results = await client.execute_paginated_view_queries(
        "query($paragraphId: Int!, $page: Int!) { view { nodes { paragraphId } } }",
        [{"paragraphId": 123}, {"paragraphId": 456}],
    )

    assert results == [
        [{"paragraphId": 123}],
        [{"paragraphId": 456}],
    ]
    assert maximum_active_queries == 2


@pytest.mark.asyncio
async def test_execute_paginated_view_query_rejects_invalid_page_count():
    client = DvOClient(api_url=API_URL, headers={})
    client.execute_query = AsyncMock(
        return_value={
            "view": {
                "nodes": [],
                "pagination": {"totalPages": None},
            }
        }
    )

    with pytest.raises(DvOResponseError):
        await client.execute_paginated_view_query("query { view { nodes { id } } }")


@pytest.mark.asyncio
async def test_execute_paginated_view_queries_propagates_request_errors():
    client = DvOClient(api_url=API_URL, headers={})
    client.execute_query = AsyncMock(side_effect=RuntimeError("DvO is unavailable"))

    with pytest.raises(RuntimeError, match="DvO is unavailable"):
        await client.execute_paginated_view_queries(
            "query($paragraphId: Int!, $page: Int!) { view { nodes { id } } }",
            [{"paragraphId": 123}, {"paragraphId": 456}],
        )
