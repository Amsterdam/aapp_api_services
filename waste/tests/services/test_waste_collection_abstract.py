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
from waste.models import WasteCollectionException, WasteCollectionRouteName
from waste.serializers.waste_guide_serializers import WasteDataSerializer
from waste.services.waste_collection_abstract import WasteCollectionAbstractService
from waste.tests.mock_data import (
    frequency_monthly,
    frequency_unknown,
    frequency_weekly,
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

    def test_get_dates_for_waste_item_weekly_frequency_no_exception(self):
        item = frequency_weekly.MOCK_DATA["_embedded"]["afvalwijzer"][0]
        serializer = WasteDataSerializer(data=item)
        serializer.is_valid()
        dates = self.service.get_dates_for_waste_item(item=serializer.validated_data)
        expected_dates = [
            date(2025, 12, 10),
            date(2025, 12, 17),
            date(2025, 12, 24),
            date(2025, 12, 31),
            date(2026, 1, 7),
            date(2026, 1, 14),
        ]
        self.assertEqual(dates, expected_dates)

    def test_get_dates_for_waste_item_weekly_frequency_single_exception(self):
        exception_route_name_instance = baker.make(
            WasteCollectionRouteName, name="Met_Uitzondering_Rest"
        )
        baker.make(
            WasteCollectionException,
            date="2025-12-24",
            affected_routes=[exception_route_name_instance],
        )

        item = frequency_weekly.MOCK_DATA["_embedded"]["afvalwijzer"][0]
        serializer = WasteDataSerializer(data=item)
        serializer.is_valid()
        dates = self.service.get_dates_for_waste_item(item=serializer.validated_data)
        expected_dates = [
            date(2025, 12, 10),
            date(2025, 12, 17),
            date(2025, 12, 31),
            date(2026, 1, 7),
            date(2026, 1, 14),
        ]
        self.assertEqual(dates, expected_dates)

    def test_get_dates_for_waste_item_weekly_frequency_multiple_exceptions(self):
        exception_route_name_instance = baker.make(
            WasteCollectionRouteName, name="Met_Uitzondering_Rest"
        )

        baker.make(
            WasteCollectionException,
            date="2025-12-24",
            affected_routes=[exception_route_name_instance],
        )
        baker.make(
            WasteCollectionException,
            date="2026-01-07",
            affected_routes=[exception_route_name_instance],
        )

        item = frequency_weekly.MOCK_DATA["_embedded"]["afvalwijzer"][0]
        serializer = WasteDataSerializer(data=item)
        serializer.is_valid()
        dates = self.service.get_dates_for_waste_item(item=serializer.validated_data)
        expected_dates = [
            date(2025, 12, 10),
            date(2025, 12, 17),
            date(2025, 12, 31),
            date(2026, 1, 14),
        ]
        self.assertEqual(dates, expected_dates)

    def test_get_dates_for_waste_item_weekly_frequency_all_exceptions(self):
        exception_route_name_instance = baker.make(
            WasteCollectionRouteName, name="Met_Uitzondering_Rest"
        )

        all_dates = [
            date(2025, 12, 10),
            date(2025, 12, 17),
            date(2025, 12, 24),
            date(2025, 12, 31),
            date(2026, 1, 7),
            date(2026, 1, 14),
        ]
        for d in all_dates:
            baker.make(
                WasteCollectionException,
                date=d,
                affected_routes=[exception_route_name_instance],
            )

        item = frequency_weekly.MOCK_DATA["_embedded"]["afvalwijzer"][0]
        serializer = WasteDataSerializer(data=item)
        serializer.is_valid()
        dates = self.service.get_dates_for_waste_item(item=serializer.validated_data)
        expected_dates = []
        self.assertEqual(dates, expected_dates)
