from urllib.parse import urlencode

import aiohttp
import pytest
from aioresponses import aioresponses

from contact.services.address import AddressService
from contact.tests.mock_data import address
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class AddressServiceTest(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.service = AddressService()

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        api_response = address.MOCK_DATA
        renamed_api_response = self.service._rename_fields_for_serializer(
            api_response["response"]["docs"][0]
        )

        params = [
            (
                "fl",
                "straatnaam huisnummer huisletter huisnummertoevoeging postcode woonplaatsnaam type nummeraanduiding_id centroide_ll",
            ),
            (
                "qf",
                "exacte_match^1 suggest^0.5 straatnaam^0.6 huisnummer^0.5 huisletter^0.5 huisnummertoevoeging^0.5",
            ),
            ("fq", "bron:BAG"),
            ("bq", "type:weg^1.5"),
            ("bq", "type:adres^1"),
            ("lat", 52.1236451),
            ("lon", 4.12369605),
            ("fq", "type:adres"),
            ("rows", "1"),
        ]
        query_string = urlencode(params)
        url_with_params = f"{self.service.url}?{query_string}"
        with aioresponses() as mocked:
            mocked.get(url_with_params, payload=api_response)

            async with aiohttp.ClientSession() as session:
                result = await self.service._async_get_address_by_coordinates(
                    session, latitude=52.1236451, longitude=4.12369605
                )

                assert result == renamed_api_response

    def test_rename_fields_for_serializer(self):

        input_data = address.MOCK_DATA["response"]["docs"][0]
        expected_output = {
            "type": "adres",
            "woonplaatsnaam": "Amsterdam",
            "postcode": "1023AB",
            "centroide_ll": "POINT(4.12369605 52.1236451)",
            "nummeraanduiding_id": "123",
            "huisnummer": 123,
            "straatnaam": "straatnaam",
            "city": "Amsterdam",
            "street": "straatnaam",
            "lat": 52.1236451,
            "lon": 4.12369605,
            "number": 123,
            "bagId": "123",
        }

        result = self.service._rename_fields_for_serializer(input_data)
        print(result)
        assert result == expected_output
