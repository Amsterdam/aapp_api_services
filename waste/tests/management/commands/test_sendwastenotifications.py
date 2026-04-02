from unittest.mock import patch

import responses
from django.conf import settings
from django.core.management import call_command
from freezegun import freeze_time
from model_bakery import baker

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import WasteDevice
from waste.models import WasteCollectionException, WasteCollectionRouteName
from waste.tests.mock_data import (
    frequency_four_weeks,
    frequency_hardcoded_with_year,
    frequency_hardcoded_wo_year,
    frequency_monthly,
    frequency_none,
    frequency_weekly,
    frequency_weekly_oneven,
)


@patch("waste.management.commands.sendwastenotifications.NotificationService.send")
class SendWasteNotificationsTest(ResponsesActivatedAPITestCase):
    """
    Different addresses have different frequencies on which the waste is collected.
    For all these frequencies we have a testcase where the notification should be send
    and a testcase where the notification should not be send.
    """

    @freeze_time("2025-03-31")
    def test_send_single_notification_weekly_pattern_send(
        self, mock_call_notification_service
    ):
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_none.MOCK_DATA)
        schedule = baker.make(
            WasteDevice, bag_nummeraanduiding_id="12345", updated_at=None
        )
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_called_with(
            device_ids=[schedule.device_id],
            waste_type="Groente, fruit, etensresten en tuinafval",
        )

    @freeze_time("2025-03-31")
    def test_send_single_notification_weekly_pattern_not_send_exception(
        self, mock_call_notification_service
    ):
        exception_route_name_instance = baker.make(
            WasteCollectionRouteName, name="Met_Uitzondering"
        )
        baker.make(
            WasteCollectionException,
            date="2025-04-01",
            affected_routes=[exception_route_name_instance],
        )
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_none.MOCK_DATA)
        baker.make(WasteDevice, bag_nummeraanduiding_id="12345", updated_at=None)
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_not_called()

    @freeze_time("2025-03-30")
    def test_send_single_notification_weekly_pattern_not_send_schedule(
        self, mock_call_notification_service
    ):
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_none.MOCK_DATA)
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_not_called()

    @freeze_time("2026-03-19")
    def test_send_single_notification_four_pattern_send(
        self, mock_call_notification_service
    ):
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_four_weeks.MOCK_DATA)
        schedule = baker.make(
            WasteDevice, bag_nummeraanduiding_id="12345", updated_at=None
        )
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_called_with(
            device_ids=[schedule.device_id],
            waste_type="Papier en karton",
        )

    @freeze_time("2026-03-12")
    def test_send_single_notification_four_pattern_not_send(
        self, mock_call_notification_service
    ):
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_four_weeks.MOCK_DATA)
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_not_called()

    @freeze_time("2026-01-08")
    def test_send_single_notification_with_year_pattern_send(
        self, mock_call_notification_service
    ):
        responses.get(
            settings.WASTE_GUIDE_URL, json=frequency_hardcoded_with_year.MOCK_DATA
        )
        schedule = baker.make(
            WasteDevice, bag_nummeraanduiding_id="bagId", updated_at=None
        )
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_called_with(
            device_ids=[schedule.device_id],
            waste_type="Papier en karton",
        )

    @freeze_time("2026-01-15")
    def test_send_single_notification_with_year_pattern_not_send(
        self, mock_call_notification_service
    ):
        responses.get(
            settings.WASTE_GUIDE_URL, json=frequency_hardcoded_with_year.MOCK_DATA
        )
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_not_called()

    @freeze_time("2026-03-05")
    def test_send_single_notification_wo_year_pattern_send(
        self, mock_call_notification_service
    ):
        responses.get(
            settings.WASTE_GUIDE_URL, json=frequency_hardcoded_wo_year.MOCK_DATA
        )
        schedule = baker.make(
            WasteDevice, bag_nummeraanduiding_id="bagId", updated_at=None
        )
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_called_with(
            device_ids=[schedule.device_id],
            waste_type="Papier en karton",
        )

    @freeze_time("2026-03-12")
    def test_send_single_notification_wo_year_pattern_not_send(
        self, mock_call_notification_service
    ):
        responses.get(
            settings.WASTE_GUIDE_URL, json=frequency_hardcoded_wo_year.MOCK_DATA
        )
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_not_called()

    @freeze_time("2026-03-08")
    def test_send_single_notification_monthly_pattern_send(
        self, mock_call_notification_service
    ):
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_monthly.MOCK_DATA)
        schedule = baker.make(WasteDevice, bag_nummeraanduiding_id="x", updated_at=None)
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_called_with(
            device_ids=[schedule.device_id],
            waste_type="Papier en karton",
        )

    @freeze_time("2026-03-08")
    def test_send_single_notification_monthly_pattern_not_send_exception(
        self, mock_call_notification_service
    ):
        exception_route_name_instance = baker.make(
            WasteCollectionRouteName, name="Met_Uitzondering"
        )
        baker.make(
            WasteCollectionException,
            date="2026-03-09",
            affected_routes=[exception_route_name_instance],
        )
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_monthly.MOCK_DATA)
        baker.make(WasteDevice, bag_nummeraanduiding_id="x", updated_at=None)
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_not_called()

    @freeze_time("2026-03-15")
    def test_send_single_notification_monthly_pattern_not_send(
        self, mock_call_notification_service
    ):
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_monthly.MOCK_DATA)
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_not_called()

    @freeze_time("2026-03-16")
    def test_send_single_notification_weekly_even_pattern_send(
        self, mock_call_notification_service
    ):
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_weekly_oneven.MOCK_DATA)
        schedule = baker.make(
            WasteDevice, bag_nummeraanduiding_id="1234", updated_at=None
        )
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_called_with(
            device_ids=[schedule.device_id],
            waste_type="Groente fruit en tuin",
        )

    @freeze_time("2026-03-09")
    def test_send_single_notification_weekly_even_pattern_not_send(
        self, mock_call_notification_service
    ):
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_weekly_oneven.MOCK_DATA)
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_not_called()

    @freeze_time("2026-03-08")
    def test_send_single_notification_weekly_odd_pattern_send(
        self, mock_call_notification_service
    ):
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_weekly_oneven.MOCK_DATA)
        schedule = baker.make(
            WasteDevice, bag_nummeraanduiding_id="1234", updated_at=None
        )
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_called_with(
            device_ids=[schedule.device_id],
            waste_type="Papier en karton",
        )

    @freeze_time("2026-03-08")
    def test_send_single_notification_weekly_odd_pattern_not_send_exception(
        self, mock_call_notification_service
    ):
        exception_route_name_instance = baker.make(
            WasteCollectionRouteName, name="Met_Uitzondering"
        )
        baker.make(
            WasteCollectionException,
            date="2026-03-09",
            affected_routes=[exception_route_name_instance],
        )
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_weekly_oneven.MOCK_DATA)
        baker.make(WasteDevice, bag_nummeraanduiding_id="1234", updated_at=None)
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_not_called()

    @freeze_time("2026-03-15")
    def test_send_single_notification_weekly_odd_pattern_not_send(
        self, mock_call_notification_service
    ):
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_weekly_oneven.MOCK_DATA)
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_not_called()

    def test_add_route_names_empty_table(self, mock_call_notification_service):
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_weekly.MOCK_DATA)
        call_command("sendwastenotifications")
        all_waste_collection_route_names = WasteCollectionRouteName.objects.values_list(
            "name", flat=True
        )
        self.assertEqual(len(all_waste_collection_route_names), 2)
        self.assertEqual(
            set(all_waste_collection_route_names),
            {"Met_Uitzondering_Grof", "Met_Uitzondering_Rest"},
        )

    def test_add_route_names_existing_name_overlap(
        self, mock_call_notification_service
    ):
        baker.make(WasteCollectionRouteName, name="Met_Uitzondering_Grof")
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_weekly.MOCK_DATA)
        call_command("sendwastenotifications")
        all_waste_collection_route_names = WasteCollectionRouteName.objects.values_list(
            "name", flat=True
        )
        self.assertEqual(len(all_waste_collection_route_names), 2)
        self.assertEqual(
            set(all_waste_collection_route_names),
            {"Met_Uitzondering_Grof", "Met_Uitzondering_Rest"},
        )

    def test_add_route_names_existing_name_no_overlap(
        self, mock_call_notification_service
    ):
        baker.make(WasteCollectionRouteName, name="Met_Uitzondering_Papier")
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_weekly.MOCK_DATA)
        call_command("sendwastenotifications")
        all_waste_collection_route_names = WasteCollectionRouteName.objects.values_list(
            "name", flat=True
        )
        self.assertEqual(len(all_waste_collection_route_names), 3)
        self.assertEqual(
            set(all_waste_collection_route_names),
            {
                "Met_Uitzondering_Grof",
                "Met_Uitzondering_Rest",
                "Met_Uitzondering_Papier",
            },
        )
