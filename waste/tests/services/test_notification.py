from datetime import timedelta

import freezegun
from django.contrib.auth.models import User
from django.utils import timezone
from model_bakery import baker

from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models.notification_models import Device, ScheduledNotification
from notification.models.waste_guide_models import WasteDevice
from waste.models import ManualNotification
from waste.services.notification import ManualNotificationService, NotificationService


@freezegun.freeze_time("2021-08-01")
class NotificationServiceTest(ResponsesActivatedAPITestCase):
    def test_call_notification_service(self):
        notification_service = NotificationService()
        notification_service.send(
            device_ids=["device1", "device2"],
            waste_type="glas",
        )

        notification = ScheduledNotification.objects.first()
        self.assertEqual(notification.title, "Afvalwijzer")
        self.assertIn("Morgen halen we glas in uw buurt op.", notification.body)
        self.assertEqual(notification.module_slug, "waste-guide")
        self.assertEqual(notification.notification_type, "waste-guide:date-reminder")
        devices = set(notification.devices.values_list("external_id", flat=True))
        self.assertEqual(devices, {"device1", "device2"})


class ManualNotificationServiceTest(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.notification_service = ManualNotificationService()

        for suffix in ["1", "2", "3"]:
            Device.objects.create(
                external_id=f"device{suffix}", os="ios", firebase_token=None
            )
            WasteDevice.objects.create(
                device_id=f"device{suffix}", bag_nummeraanduiding_id=f"bag-{suffix}"
            )

        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.notification_service = ManualNotificationService()

    def test_call_notification_service(self):
        scheduled_for = timezone.now() + timedelta(days=1)
        notification = ManualNotification.objects.create(
            title="Vanaf morgen kun je de kerstbook aan de straat zetten",
            message="Zorg dat je hem op de goede plek zet",
            created_by=self.user,
            send_at=scheduled_for,
        )

        self.notification_service.send(notification=notification)

        notification.refresh_from_db()
        scheduled_notification = ScheduledNotification.objects.get()
        self.assertEqual(
            scheduled_notification.title,
            "Vanaf morgen kun je de kerstbook aan de straat zetten",
        )
        self.assertEqual(
            scheduled_notification.body, "Zorg dat je hem op de goede plek zet"
        )
        self.assertEqual(scheduled_notification.module_slug, "waste-guide")
        self.assertEqual(
            scheduled_notification.notification_type, "waste-guide:manual-notification"
        )
        self.assertEqual(scheduled_notification.scheduled_for, scheduled_for)
        self.assertEqual(
            scheduled_notification.identifier,
            self.notification_service._create_identifier(notification.id),
        )
        self.assertEqual(notification.send_at, scheduled_for)
        self.assertEqual(notification.nr_sessions, 3)
        devices = set(
            scheduled_notification.devices.values_list("external_id", flat=True)
        )
        self.assertEqual(devices, {"device1", "device2", "device3"})

    def test_call_notification_service_updates_existing_schedule(self):
        initial_send_at = timezone.now() + timedelta(days=1)
        updated_send_at = initial_send_at + timedelta(hours=2)
        notification = ManualNotification.objects.create(
            title="Eerste titel",
            message="Eerste bericht",
            created_by=self.user,
            send_at=initial_send_at,
        )

        self.notification_service.send(notification=notification)

        notification.title = "Bijgewerkte titel"
        notification.message = "Bijgewerkt bericht"
        notification.send_at = updated_send_at
        notification.save(update_fields=["title", "message", "send_at"])

        self.notification_service.send(notification=notification)

        scheduled_notification = ScheduledNotification.objects.get()
        self.assertEqual(ScheduledNotification.objects.count(), 1)
        self.assertEqual(scheduled_notification.title, "Bijgewerkte titel")
        self.assertEqual(scheduled_notification.body, "Bijgewerkt bericht")
        self.assertEqual(scheduled_notification.scheduled_for, updated_send_at)
        self.assertEqual(
            scheduled_notification.identifier,
            self.notification_service._create_identifier(notification.id),
        )

    def test_delete_notification_removes_existing_schedule(self):
        notification = baker.make(
            ManualNotification,
            created_by=self.user,
            send_at=timezone.now() + timedelta(days=1),
        )

        self.notification_service.send(notification=notification)

        self.notification_service.delete_notification(notification)

        self.assertFalse(ScheduledNotification.objects.exists())

    def test_error_raised_if_notification_not_saved(self):
        notification = ManualNotification(
            title="Test",
            message="Test message",
            created_by=self.user,
            send_at=timezone.now() + timedelta(days=1),
        )

        with self.assertRaises(ValueError):
            self.notification_service._create_identifier(notification.id)
