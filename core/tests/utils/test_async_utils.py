from unittest.mock import patch

import pytest
from aioresponses import aioresponses

from core.utils.async_utils import async_fetch


@pytest.mark.asyncio
async def test_fetch_success():
    url = "http://example.com/api/item/1"
    api_response = {"id": 1, "data": "some data"}

    with aioresponses() as mocked:
        mocked.get(url, payload=api_response)

        result = await async_fetch([url])

    assert result == [api_response]


@pytest.mark.asyncio
async def test_fetch_retries_and_fails():
    url = "http://example.com/api/item/1"

    with aioresponses() as mocked:
        mocked.get(url, status=500, repeat=True)

        with patch("tenacity.nap.sleep", return_value=None):
            result = await async_fetch([url])

    assert result == [None]
    # Ensure that the retry mechanism was triggered by checking the number of requests made
    assert sum(len(calls) for calls in mocked.requests.values()) == 3
