import re
from datetime import date

import freezegun
import responses
from django.conf import settings
from django.test import override_settings
from model_bakery import baker

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from waste.models import WasteCollectionException, WasteCollectionRouteName
from waste.services.waste_collection_pdf import WasteCollectionPDFService
from waste.tests.mock_data import frequency_weekly


@freezegun.freeze_time("2025-12-09")
class WasteCollectionPDFServiceTest(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.service = WasteCollectionPDFService()
        responses.get(
            re.compile(settings.WASTE_GUIDE_URL + ".*"),
            json=frequency_weekly.MOCK_DATA,
        )

    @override_settings(CALENDAR_LENGTH=14)
    def test_create_pdf_calendar_dates(self):
        validated_data = self.service.get_validated_data_for_bag_id(bag_id="1234")

        waste_collection_by_date, _ = self.service.create_pdf_calendar_dates(
            validated_data
        )
        self.assertEqual(len(waste_collection_by_date), 6)
        self.assertEqual(waste_collection_by_date[date(2025, 12, 10)], ["Rest", "GA"])

    @override_settings(CALENDAR_LENGTH=14)
    def test_create_pdf_calendar_dates_with_single_exception(self):
        exception_route_name_instance = baker.make(
            WasteCollectionRouteName, name="Met_Uitzondering_Rest"
        )
        baker.make(
            WasteCollectionException,
            date="2025-12-10",
            affected_routes=[exception_route_name_instance],
        )

        validated_data = self.service.get_validated_data_for_bag_id(bag_id="1234")
        waste_collection_by_date, _ = self.service.create_pdf_calendar_dates(
            validated_data
        )
        self.assertEqual(len(waste_collection_by_date), 6)
        self.assertEqual(waste_collection_by_date[date(2025, 12, 10)], ["GA"])

    @override_settings(CALENDAR_LENGTH=14)
    def test_create_pdf_calendar_dates_with_multiple_exceptions(self):
        exception_route_name_instance_rest = baker.make(
            WasteCollectionRouteName, name="Met_Uitzondering_Rest"
        )
        exception_route_name_instance_grof = baker.make(
            WasteCollectionRouteName, name="Met_Uitzondering_Grof"
        )
        baker.make(
            WasteCollectionException,
            date="2025-12-10",
            affected_routes=[
                exception_route_name_instance_rest,
                exception_route_name_instance_grof,
            ],
        )

        validated_data = self.service.get_validated_data_for_bag_id(bag_id="1234")
        waste_collection_by_date, _ = self.service.create_pdf_calendar_dates(
            validated_data
        )
        self.assertEqual(len(waste_collection_by_date), 5)
