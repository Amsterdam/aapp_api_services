from datetime import datetime

from aioresponses import aioresponses
from django.conf import settings

from construction_work.etl.extract_data import (
    get_all_iprox_items,
    get_iprox_items_data,
)
from core.testing_aioresponses import patch_client_response_init

patch_client_response_init()


def test_get_all_iprox_items_success():
    iprox_url = "http://example.com/api/items"

    # Mock data returned by the API
    api_response = [
        {"id": 1, "modified": "2023-10-01T12:34:56+0100"},
        {"id": 2, "modified": "2023-10-02T12:34:56+0100"},
    ]

    expected_result = [
        {
            "id": 1,
            "modified": datetime.strptime(
                "2023-10-01T12:34:56+0100", settings.DATE_FORMAT_IPROX
            ),
        },
        {
            "id": 2,
            "modified": datetime.strptime(
                "2023-10-02T12:34:56+0100", settings.DATE_FORMAT_IPROX
            ),
        },
    ]

    with aioresponses() as mocked:
        mocked.get(iprox_url, payload=api_response)

        result = get_all_iprox_items(iprox_url)
        assert result == expected_result


def test_get_all_iprox_items_non_200_status():
    iprox_url = "http://example.com/api/items"

    with aioresponses() as mocked:
        mocked.get(iprox_url, status=500)

        result = get_all_iprox_items(iprox_url)
        assert result is None


def test_get_iprox_items_data_success():
    base_url = "http://example.com/api/items/"
    item_ids = [1, 2]

    expected_urls = [f"{base_url}{item_id}" for item_id in item_ids]

    # Mock data for each item
    api_responses = [{"id": 1, "data": "Item 1 Data"}, {"id": 2, "data": "Item 2 Data"}]

    with aioresponses() as mocked:
        # Mock each item URL with corresponding response
        for url, response in zip(expected_urls, api_responses, strict=True):
            mocked.get(url, payload=response)

        result = get_iprox_items_data(base_url, item_ids)
        assert result == api_responses


def test_get_iprox_items_data_partial_failure():
    base_url = "http://example.com/api/items/"
    item_ids = [1, 2]

    expected_urls = [f"{base_url}{item_id}" for item_id in item_ids]

    api_responses = [
        {"id": 1, "data": "Item 1 Data"},
        None,  # Simulate failure for the second item
    ]

    with aioresponses() as mocked:
        # Mock successful response for the first item
        mocked.get(expected_urls[0], payload=api_responses[0])
        # Mock failure for the second item
        mocked.get(expected_urls[1], status=500)

        result = get_iprox_items_data(base_url, item_ids)
        # Should only include the successful item
        assert result == [api_responses[0]]
