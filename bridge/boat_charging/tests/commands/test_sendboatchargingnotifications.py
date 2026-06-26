from datetime import datetime
from zoneinfo import ZoneInfo

import freezegun
from django.conf import settings
from django.core.management import call_command
from django.test import override_settings
from model_bakery import baker

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import (
    BoatChargingDevice,
    Device,
    ScheduledNotification,
)

tz = ZoneInfo(settings.TIME_ZONE)


class TestCommand(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.device_id = "device1"
        self.device = baker.make(
            Device, external_id=self.device_id, os="ios", firebase_token=None
        )

        with freezegun.freeze_time(datetime(2026, 6, 2, 7, 15, 0, tzinfo=tz)):
            self.notification = baker.make(
                BoatChargingDevice,
                session_id="some_session_id",
                device_id=self.device_id,
            )

    @override_settings(
        BOAT_CHARGING_NOTIFICATION_SETTINGS={
            "thresholds": "1H,2H",
            "repeat_every": "1H",
        }
    )
    @freezegun.freeze_time(
        datetime(2026, 6, 2, 8, 30, 0, tzinfo=tz)
    )  # 1 hour and 15 minutes later
    def test_command_threshold_passed(self):

        call_command("sendboatchargingnotifications")

        self.assertEqual(
            ScheduledNotification.objects.count(), 1
        )  # Threshold passed, so one notification should be sent
