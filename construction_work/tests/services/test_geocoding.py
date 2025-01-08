from unittest.mock import patch

import requests
from django.test import TestCase

from construction_work.services.geocoding import geocode_address


class TestGeocodeAddress(TestCase):
    @patch('requests.get')
    def test_successful_geocoding(self, mock_get):
        mock_response = mock_get.return_value
        result = [4.893604, 52.373169]
        mock_response.json.return_value = {
            "results": [{
                "centroid": result  # longitude, latitude for Dam Square
            }]
        }

        lat, lon = geocode_address("Dam 1")

        assert lat == result[1]
        assert lon == result[0]
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_multiple_results_returns_first_result(self, mock_get):
        mock_response = mock_get.return_value
        first_result = [4.89371756804882, 52.37329259746784]  # Dam Square
        mock_response.json.return_value = {
            "results": [
                {"centroid": first_result},
                {"centroid": [4.894108670308143, 52.37307409090358]}   # Nieuwe Kerk
            ]
        }

        lat, lon = geocode_address("Dam")  # Ambiguous address

        assert lat == first_result[1]  # First result's latitude 
        assert lon == first_result[0]  # First result's longitude

    @patch('requests.get')
    def test_no_results_returns_none(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"results": []}

        lat, lon = geocode_address("Niet Bestaande Straat 123")

        assert lat is None
        assert lon is None

    @patch('requests.get')
    def test_request_exception_returns_none(self, mock_get):
        mock_get.side_effect = requests.RequestException("Connection error")

        lat, lon = geocode_address("Damrak 1")

        assert lat is None
        assert lon is None
