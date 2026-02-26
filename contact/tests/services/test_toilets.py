import json
from unittest.mock import patch

import responses
from django.conf import settings
from requests import Response

from contact.enums.toilets import ToiletFilters, ToiletProperties
from contact.services.toilets import ToiletService
from contact.tests.mock_data import toilets
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class ToiletServiceTest(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.service = ToiletService()

    def test_get_full_data(self):
        responses.get(settings.PUBLIC_TOILET_URL, json=toilets.MOCK_DATA)

        full_data = self.service.get_full_data()

        self.assertEqual(full_data["filters"], ToiletFilters.choices())
        self.assertEqual(full_data["properties_to_include"], ToiletProperties.choices())
        self.assertEqual(len(full_data["data"]), len(toilets.MOCK_DATA["features"]))

    @patch("contact.services.toilets.requests.get")
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
            {"content": toilets.MOCK_DATA, "status": "SUCCESS"}
        ).encode("utf-8")

        mock_get.side_effect = [mock_response_1, mock_response_2]

        resp = self.service._make_request()
        self.assertEqual(resp.status_code, 200)
