import datetime
from unittest.mock import patch

import responses
from django.conf import settings
from django.core.management import call_command
from freezegun import freeze_time
from model_bakery import baker

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from waste.models import NotificationSchedule
from waste.tests.mock_data import (
    frequency_four_weeks,
    frequency_hardcoded_with_year,
    frequency_hardcoded_wo_year,
    frequency_monthly,
    frequency_none,
    frequency_weekly_oneven,
)


@patch(
    "waste.management.commands.sendwastenotifications.NotificationService.send_waste_notification"
)
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
            NotificationSchedule, bag_nummeraanduiding_id="12345", updated_at=None
        )
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_called_with(
            device_ids=[schedule.device_id],
            waste_type="Groente, fruit, etensresten en tuinafval",
            notification_datetime=datetime.datetime(2025, 3, 31, 21, 0),
        )

    @freeze_time("2025-03-30")
    def test_send_single_notification_weekly_pattern_not_send(
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
            NotificationSchedule, bag_nummeraanduiding_id="12345", updated_at=None
        )
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_called_with(
            device_ids=[schedule.device_id],
            waste_type="Papier en karton",
            notification_datetime=datetime.datetime(2026, 3, 19, 21, 0),
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
            NotificationSchedule, bag_nummeraanduiding_id="bagId", updated_at=None
        )
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_called_with(
            device_ids=[schedule.device_id],
            waste_type="Papier en karton",
            notification_datetime=datetime.datetime(2026, 1, 8, 21, 0),
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
            NotificationSchedule, bag_nummeraanduiding_id="bagId", updated_at=None
        )
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_called_with(
            device_ids=[schedule.device_id],
            waste_type="Papier en karton",
            notification_datetime=datetime.datetime(2026, 3, 5, 21, 0),
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
        schedule = baker.make(
            NotificationSchedule, bag_nummeraanduiding_id="x", updated_at=None
        )
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_called_with(
            device_ids=[schedule.device_id],
            waste_type="Papier en karton",
            notification_datetime=datetime.datetime(2026, 3, 8, 21, 0),
        )

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
            NotificationSchedule, bag_nummeraanduiding_id="1234", updated_at=None
        )
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_called_with(
            device_ids=[schedule.device_id],
            waste_type="Groente fruit en tuin",
            notification_datetime=datetime.datetime(2026, 3, 16, 21, 0),
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
            NotificationSchedule, bag_nummeraanduiding_id="1234", updated_at=None
        )
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_called_with(
            device_ids=[schedule.device_id],
            waste_type="Papier en karton",
            notification_datetime=datetime.datetime(2026, 3, 8, 21, 0),
        )

    @freeze_time("2026-03-15")
    def test_send_single_notification_weekly_odd_pattern_not_send(
        self, mock_call_notification_service
    ):
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_weekly_oneven.MOCK_DATA)
        call_command("sendwastenotifications")
        mock_call_notification_service.assert_not_called()
