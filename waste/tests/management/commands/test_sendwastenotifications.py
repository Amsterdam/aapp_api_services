import datetime
from unittest.mock import patch

import responses
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from freezegun import freeze_time
from model_bakery import baker

from waste.models import NotificationSchedule
from waste.tests.mock_data import frequency_none


@freeze_time("2025-03-31")
@patch(
    "waste.management.commands.sendwastenotifications.NotificationService.send_waste_notification"
)
class SendWasteNotificationsTest(TestCase):
    @responses.activate
    def test_send_single_notification(self, mock_call_notification_service):
        responses.get(settings.WASTE_GUIDE_URL, json=frequency_none.MOCK_DATA)
        schedule = baker.make(
            NotificationSchedule, bag_nummeraanduiding_id="12345", updated_at=None
        )

        call_command("sendwastenotifications")

        mock_call_notification_service.assert_called_with(
            device_ids=[schedule.device_id],
            waste_type="Groente-, fruit-, etensresten en tuinafval",
            notification_datetime=datetime.datetime(2025, 3, 31, 21, 0),
        )
