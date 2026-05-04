from unittest.mock import patch

import requests
from django.test import TestCase

from construction_work.services.geocoding import geocode_address
from construction_work.tests.mock_data import address_search


class TestGeocodeAddress(TestCase):
    @patch("requests.get")
    def test_successful_geocoding(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = address_search.MOCK_DATA_SINGLE

        lat, lon = geocode_address("Dam 1")

        assert lat == 52.37329259
        assert lon == 4.8937175
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_no_results_returns_none(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = address_search.MOCK_DATA_NONE

        lat, lon = geocode_address("Niet Bestaande Straat 123")

        assert lat is None
        assert lon is None

    @patch("requests.get")
    def test_request_exception_returns_none(self, mock_get):
        mock_get.side_effect = requests.RequestException("Connection error")

        lat, lon = geocode_address("Damrak 1")

        assert lat is None
        assert lon is None
