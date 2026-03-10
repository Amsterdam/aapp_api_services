import json
from unittest.mock import patch
from urllib.parse import urlencode

import responses
from requests import Response

from contact.services.address import AddressService
from contact.tests.mock_data import address
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class AddressServiceTest(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.service = AddressService()
        self.api_success_response = address.MOCK_DATA
        self.api_invalid_json_response = "Invalid JSON"
        self.api_missing_response = {"data": {}}
        self.api_invalid_response = {"response": {"something_random": []}}
        self.latitude = 52.1236451
        self.longitude = 4.12369605

    def test_get_address_by_coordinates(self):
        latitude = 52.1236450
        longitude = 4.12369600
        url_with_params = f"{self.service.url}?{urlencode(self.service.construct_params(latitude=latitude, longitude=longitude))}"

        responses.get(url_with_params, json=self.api_success_response)
        address = self.service.get_address_by_coordinates(
            latitude=latitude, longitude=longitude
        )
        assert address is not None
        assert address["street"] == "straatnaam"

    def test_get_address_by_coordinates_invalid_json(self):
        latitude = 52.1236452
        longitude = 4.12369602
        url_with_params = f"{self.service.url}?{urlencode(self.service.construct_params(latitude=latitude, longitude=longitude))}"

        responses.get(url_with_params, json=self.api_invalid_json_response)

        address = self.service.get_address_by_coordinates(
            latitude=latitude, longitude=longitude
        )
        assert address is None

    def test_get_address_by_coordinates_missing_response(self):
        latitude = 52.1236453
        longitude = 4.12369603
        url_with_params = f"{self.service.url}?{urlencode(self.service.construct_params(latitude=latitude, longitude=longitude))}"

        responses.get(url_with_params, json=self.api_missing_response)
        address = self.service.get_address_by_coordinates(
            latitude=latitude, longitude=longitude
        )
        print(address)
        assert address is None

    def test_get_address_by_coordinates_invalid_response(self):
        latitude = 52.1236454
        longitude = 4.12369604
        url_with_params = f"{self.service.url}?{urlencode(self.service.construct_params(latitude=latitude, longitude=longitude))}"

        responses.get(url_with_params, json=self.api_invalid_response)
        address = self.service.get_address_by_coordinates(
            latitude=latitude, longitude=longitude
        )
        print(address)
        assert address is None

    @patch("contact.services.address.requests.get")
    def test_make_request_succeeds_after_retry(self, mock_get):
        # Simulate a 500 error on the first request
        mock_response_1 = Response()
        mock_response_1.status_code = 500
        mock_response_1._content = json.dumps(
            {"status": "ERROR", "message": "Internal Server Error"}
        ).encode("utf-8")

        # Simulate a successful response on the second request
        mock_response_2 = Response()
        mock_response_2.status_code = 200
        mock_response_2._content = json.dumps(
            {"content": address.MOCK_DATA, "status": "SUCCESS"}
        ).encode("utf-8")

        mock_get.side_effect = [mock_response_1, mock_response_2]

        resp = self.service.make_request(
            params=self.service.construct_params(
                latitude=self.latitude, longitude=self.longitude
            )
        )
        self.assertEqual(resp.status_code, 200)

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
