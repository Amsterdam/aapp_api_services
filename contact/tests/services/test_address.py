import asyncio
from unittest.mock import patch
from urllib.parse import urlencode

import aiohttp
import pytest
from aioresponses import aioresponses
from tenacity import RetryError

from contact.services.address import AddressService
from contact.tests.mock_data import address
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class AddressServiceTest(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.service = AddressService()
        self.api_success_response = address.MOCK_DATA
        self.latitude = 52.1236451
        self.longitude = 4.12369605
        self.url_with_params = f"{self.service.url}?{urlencode(self.service.construct_params(latitude=self.latitude, longitude=self.longitude))}"

    def test_batch_get_addresses_by_coordinates(self):

        # Mock the async method to return a predefined response
        with aioresponses() as mocked:
            mocked.get(self.url_with_params, payload=self.api_success_response)

            result = self.service.batch_get_addresses_by_coordinates(
                coords=[(self.latitude, self.longitude)]
            )

            expected_result = {
                (
                    self.latitude,
                    self.longitude,
                ): self.service._rename_fields_for_serializer(
                    self.api_success_response["response"]["docs"][0]
                )
            }

            assert result == expected_result

    @pytest.mark.asyncio
    @patch("contact.services.address.AddressService._async_get_address_by_coordinates")
    async def test_fetch_with_sem_exception(self, mock_async_get):

        sem = asyncio.Semaphore(1)
        async with aiohttp.ClientSession() as session:
            mock_async_get.side_effect = Exception("Test exception")
            result = await self.service._fetch_with_sem(
                sem, session, self.latitude, self.longitude
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_async_get_address_by_coordinates_success(self):
        # api_response = address.MOCK_DATA
        renamed_api_response = self.service._rename_fields_for_serializer(
            self.api_success_response["response"]["docs"][0]
        )

        with aioresponses() as mocked:
            mocked.get(self.url_with_params, payload=self.api_success_response)

            async with aiohttp.ClientSession() as session:
                result = await self.service._async_get_address_by_coordinates(
                    session, latitude=self.latitude, longitude=self.longitude
                )

                assert result == renamed_api_response

    @pytest.mark.asyncio
    async def test_async_get_address_by_coordinates_retries_and_fails(self):

        with aioresponses() as mocked:
            mocked.get(self.url_with_params, status=500)

            async with aiohttp.ClientSession() as session:
                with pytest.raises(RetryError):
                    await self.service._async_get_address_by_coordinates(
                        session, latitude=self.latitude, longitude=self.longitude
                    )

    @pytest.mark.asyncio
    async def test_async_get_address_by_coordinates_invalid_response(self):

        with aioresponses() as mocked:
            mocked.get(self.url_with_params, payload={"data": "invalid"})

            async with aiohttp.ClientSession() as session:
                result = await self.service._async_get_address_by_coordinates(
                    session, latitude=self.latitude, longitude=self.longitude
                )

                assert result is None

    def test_rename_fields_for_serializer(self):

        input_data = address.MOCK_DATA["response"]["docs"][0]
        expected_output = {
            "type": "adres",
            "woonplaatsnaam": "Amsterdam",
            "postcode": "1023AB",
            "centroide_ll": f"POINT({self.longitude} {self.latitude})",
            "nummeraanduiding_id": "123",
            "huisnummer": 123,
            "straatnaam": "straatnaam",
            "city": "Amsterdam",
            "street": "straatnaam",
            "lat": self.latitude,
            "lon": self.longitude,
            "number": 123,
            "bagId": "123",
        }

        result = self.service._rename_fields_for_serializer(input_data)
        assert result == expected_output

    def test_get_lat_lon_from_coordinates(self):
        coordinates = f"POINT({self.longitude} {self.latitude})"
        expected_result = (self.latitude, self.longitude)

        result = self.service._get_lat_and_lon_from_coordinates(coordinates)
        assert result == expected_result

    def test_get_lat_lon_from_coordinates_invalid_format(self):
        coordinates = "INVALID_FORMAT"

        result = self.service._get_lat_and_lon_from_coordinates(coordinates)
        assert result == (None, None)

    def test_get_lat_lon_from_coordinates_coords(self):
        class CoordinatesObject:
            def __init__(self, latitude, longitude):
                self.coords = [longitude, latitude]

        coordinates = CoordinatesObject(self.latitude, self.longitude)

        result = self.service._get_lat_and_lon_from_coordinates(coordinates)
        assert result == (self.latitude, self.longitude)
