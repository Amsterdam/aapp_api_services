import json
import re
from datetime import date
from unittest.mock import patch

import freezegun
import responses
from django.conf import settings
from django.test import override_settings
from requests import Response

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from waste.exceptions import WasteGuideException
from waste.services.waste_collection_abstract import WasteCollectionAbstractService
from waste.tests.mock_data import (
    frequency_monthly,
    frequency_unknown,
)


@freezegun.freeze_time("2025-12-09")
class WasteCollectionAbstractServiceTest(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.service = WasteCollectionAbstractService(bag_nummeraanduiding_id="1234")

    @override_settings(CALENDAR_LENGTH=7)
    def test_get_dates(self):
        dates = self.service._get_dates()
        expected_dates = [
            date(2025, 12, 9),
            date(2025, 12, 10),
            date(2025, 12, 11),
            date(2025, 12, 12),
            date(2025, 12, 13),
            date(2025, 12, 14),
            date(2025, 12, 15),
        ]
        self.assertEqual(dates, expected_dates)

    def test_get_validated_data(self):
        responses.get(
            re.compile(settings.WASTE_GUIDE_URL + ".*"),
            json=frequency_monthly.MOCK_DATA,
        )
        self.service.get_validated_data()
        self.assertIsNotNone(self.service.validated_data)

    def test_get_validated_data_request_exception(self):
        responses.get(
            re.compile(settings.WASTE_GUIDE_URL + ".*"),
            status=500,
        )
        with self.assertRaises(WasteGuideException):
            self.service.get_validated_data()

    @patch("waste.services.waste_collection_abstract.requests.request")
    def test_get_validated_data_succeeds_after_retry(self, mock_get):
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
            {"content": frequency_monthly.MOCK_DATA, "status": "SUCCESS"}
        ).encode("utf-8")

        mock_get.side_effect = [mock_response_1, mock_response_2]

        resp = self.service.make_request(method="GET", url="waste_guide_url")
        self.assertEqual(resp.status_code, 200)

    def test_get_dates_for_waste_item_unknown_frequency(self):
        item = frequency_unknown.MOCK_DATA["_embedded"]["afvalwijzer"][0]
        dates = self.service.get_dates_for_waste_item(item=item)
        self.assertEqual(len(dates), 0)
