from unittest.mock import patch

import responses
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings
from freezegun import freeze_time
from model_bakery import baker

from waste.models import NotificationSchedule
from waste.tests import data


@freeze_time("2024-03-31")
@override_settings(CALENDAR_LENGTH=14)
@patch("waste.management.commands.sendwastenotifications.NotificationService.send")
class SendWasteNotificationsTest(TestCase):
    @responses.activate
    def test_send_single_notification(self, mock_call_notification_service):
        responses.get(settings.WASTE_GUIDE_URL, json=data.AFVALWIJZER_DATA_MINIMAL)
        schedule = baker.make(
            NotificationSchedule, bag_nummeraanduiding_id="12345", updated_at=None
        )

        call_command("sendwastenotifications")

        mock_call_notification_service.assert_called_with(
            device_ids=[schedule.device_id], type="GFT"
        )
