from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from freezegun import freeze_time
from model_bakery import baker

from waste.models import NotificationSchedule
from waste.tests import data


@freeze_time("2024-03-31")
@override_settings(CALENDAR_LENGTH=14)
@patch("waste.management.commands.sendwastenotifications.call_notification_service")
@patch("waste.services.waste_collection.requests.get")
class SendWasteNotificationsTest(TestCase):
    def test_send_single_notification(
        self, mock_waste_get, mock_call_notification_service
    ):
        mock_waste_get.return_value.status_code = 200
        mock_waste_get.return_value.json.return_value = data.AFVALWIJZER_DATA_MINIMAL
        schedule = baker.make(
            NotificationSchedule, bag_nummeraanduiding_id="12345", updated_at=None
        )

        call_command("sendwastenotifications")

        mock_call_notification_service.assert_called_with([schedule.device_id], "GFT")
