import re
from datetime import date

import freezegun
import responses
from django.conf import settings
from django.test import override_settings

from core.tests.test_authentication import ResponsesActivatedAPITestCase
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

    def test_get_dates_for_waste_item_unknown_frequency(self):
        item = frequency_unknown.MOCK_DATA["_embedded"]["afvalwijzer"][0]
        dates = self.service.get_dates_for_waste_item(item=item)
        self.assertEqual(len(dates), 0)
