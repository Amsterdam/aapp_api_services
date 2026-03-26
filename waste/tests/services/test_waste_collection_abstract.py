import json
import re
from datetime import date
from unittest.mock import patch

import freezegun
import responses
from django.conf import settings
from django.test import override_settings
from model_bakery import baker
from requests import Response

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from waste.exceptions import WasteGuideException
from waste.models import WasteCollectionException
from waste.services.waste_collection_abstract import WasteCollectionAbstractService
from waste.tests.mock_data import (
    frequency_monthly,
    frequency_unknown,
)


@freezegun.freeze_time("2025-12-09")
class WasteCollectionAbstractServiceTest(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.service = WasteCollectionAbstractService()

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
        validated_data = self.service.get_validated_data_for_bag_id("1234")
        self.assertIsNotNone(validated_data)

    def test_get_validated_data_request_exception(self):
        responses.get(
            re.compile(settings.WASTE_GUIDE_URL + ".*"),
            status=500,
        )
        with self.assertRaises(WasteGuideException):
            self.service.get_validated_data_for_bag_id("1234")

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

        resp_json = self.service.make_request(method="GET", url="waste_guide_url")
        self.assertEqual(
            resp_json["content"]["_embedded"]["afvalwijzer"][0][
                "bagNummeraanduidingId"
            ],
            "x",
        )

    def test_get_dates_for_waste_item_unknown_frequency(self):
        item = frequency_unknown.MOCK_DATA["_embedded"]["afvalwijzer"][0]
        dates = self.service.get_dates_for_waste_item(item=item)
        self.assertEqual(len(dates), 0)

    def test_no_exception_dates(self):
        service = WasteCollectionAbstractService()
        self.assertEqual(len(service.all_dates), settings.CALENDAR_LENGTH)

    def test_single_exception_dates(self):
        baker.make(WasteCollectionException, date="2025-12-09")

        service = WasteCollectionAbstractService()
        self.assertEqual(len(service.all_dates), settings.CALENDAR_LENGTH - 1)
        self.assertNotIn(date(2025, 12, 9), service.all_dates)

    def test_multiple_exception_dates(self):
        baker.make(WasteCollectionException, date="2025-12-09")
        baker.make(WasteCollectionException, date="2025-12-15")

        service = WasteCollectionAbstractService()
        self.assertEqual(len(service.all_dates), settings.CALENDAR_LENGTH - 2)
        self.assertNotIn(date(2025, 12, 9), service.all_dates)
        self.assertNotIn(date(2025, 12, 15), service.all_dates)

    def test_all_exception_dates(self):
        for d in self.service.all_dates:
            baker.make(WasteCollectionException, date=d)

        service = WasteCollectionAbstractService()
        self.assertEqual(service.all_dates, [])
