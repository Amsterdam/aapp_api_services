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

        self.notification.refresh_from_db()
        self.assertEqual(set(self.notification.sent_notifications.keys()), {"1"})

    @override_settings(
        BOAT_CHARGING_NOTIFICATION_SETTINGS={
            "thresholds": "1H,2H",
            "repeat_every": "1H",
        }
    )
    @freezegun.freeze_time(
        datetime(2026, 6, 2, 7, 45, 0, tzinfo=tz)
    )  # 30 minutes later
    def test_command_before_threshold_does_not_send(self):
        call_command("sendboatchargingnotifications")

        self.assertEqual(ScheduledNotification.objects.count(), 0)

        self.notification.refresh_from_db()
        self.assertEqual(self.notification.sent_notifications, {})

    @override_settings(
        BOAT_CHARGING_NOTIFICATION_SETTINGS={
            "thresholds": "1H,2H",
            "repeat_every": "1H",
        }
    )
    @freezegun.freeze_time(
        datetime(2026, 6, 2, 9, 30, 0, tzinfo=tz)
    )  # 2 hours and 15 minutes later
    def test_command_sends_all_passed_base_thresholds(self):
        call_command("sendboatchargingnotifications")

        notifications = ScheduledNotification.objects.all()
        self.assertEqual(notifications.count(), 2)
        self.assertTrue(all(n.title == "Boot laden herinnering" for n in notifications))

        self.notification.refresh_from_db()
        self.assertEqual(set(self.notification.sent_notifications.keys()), {"1", "2"})

    @override_settings(
        BOAT_CHARGING_NOTIFICATION_SETTINGS={
            "thresholds": "1H,2H",
            "repeat_every": "1H",
        }
    )
    @freezegun.freeze_time(
        datetime(2026, 6, 2, 11, 30, 0, tzinfo=tz)
    )  # 4 hours and 15 minutes later
    def test_command_sends_repeat_notifications_after_last_threshold(self):
        call_command("sendboatchargingnotifications")

        self.assertEqual(ScheduledNotification.objects.count(), 4)
        self.assertEqual(
            ScheduledNotification.objects.filter(
                title="Boot laden herinnering"
            ).count(),
            2,
        )
        self.assertEqual(
            ScheduledNotification.objects.filter(
                title="Haal je boot van de laadpaal"
            ).count(),
            2,
        )

        self.notification.refresh_from_db()
        self.assertEqual(
            set(self.notification.sent_notifications.keys()), {"1", "2", "3", "4"}
        )

    @override_settings(
        BOAT_CHARGING_NOTIFICATION_SETTINGS={
            "thresholds": "1H,2H",
            "repeat_every": "1H",
        }
    )
    @freezegun.freeze_time(
        datetime(2026, 6, 2, 10, 30, 0, tzinfo=tz)
    )  # 3 hours and 15 minutes later
    def test_command_does_not_resend_existing_thresholds(self):
        self.notification.sent_notifications = {
            "1": "2026-06-02T08:15:00+00:00",
            "2": "2026-06-02T09:15:00+00:00",
        }
        self.notification.save(update_fields=["sent_notifications"])

        call_command("sendboatchargingnotifications")

        self.assertEqual(ScheduledNotification.objects.count(), 1)
        scheduled = ScheduledNotification.objects.get()
        self.assertEqual(scheduled.title, "Haal je boot van de laadpaal")

        # Running twice should remain idempotent for already-sent thresholds.
        call_command("sendboatchargingnotifications")
        self.assertEqual(ScheduledNotification.objects.count(), 1)

        self.notification.refresh_from_db()
        self.assertEqual(
            set(self.notification.sent_notifications.keys()), {"1", "2", "3"}
        )

    @override_settings(
        BOAT_CHARGING_NOTIFICATION_SETTINGS={
            "thresholds": "1H,2H",
            "repeat_every": "1H",
        }
    )
    @freezegun.freeze_time(
        datetime(2026, 6, 2, 9, 30, 0, tzinfo=tz)
    )  # 2 hours and 15 minutes later
    def test_command_skips_device_without_session(self):
        self.notification.session_id = None
        self.notification.save(update_fields=["session_id"])

        call_command("sendboatchargingnotifications")

        self.assertEqual(ScheduledNotification.objects.count(), 0)

        self.notification.refresh_from_db()
        self.assertEqual(self.notification.sent_notifications, {})
