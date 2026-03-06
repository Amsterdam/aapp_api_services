import datetime
from unittest.mock import Mock

from django.utils import timezone
from freezegun import freeze_time
from model_bakery import baker

from core.services.notification_service import NotificationData
from core.services.unified_notification_service import (
    NotificationServiceError,
    UnifiedNotificationService,
)
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import Device, Notification, NotificationLast, ScheduledNotification


@freeze_time("2026-02-01 10:00:00")
class TestUnifiedNotificationService_AbstractLike(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.module_slug = "test-slug"
        self.service = UnifiedNotificationService()
        self.service.module_slug = self.module_slug
        self.service.notification_type = "test-slug:notification"
        self.device_1 = baker.make(Device, external_id="device_1")
        self.device_2 = baker.make(Device, external_id="device_2")
        baker.make(
            NotificationLast,
            device=self.device_1,
            module_slug=self.module_slug,
            notification_scope=f"{self.module_slug}:default",
        )
        baker.make(Notification, device=self.device_1)

    def test_get_last_timestamp(self):
        result = self.service.get_last_timestamp("device_1")
        self.assertEqual(
            result, datetime.datetime(2026, 2, 1, 10, 0, tzinfo=datetime.timezone.utc)
        )

    def test_get_notifications(self):
        notifications = self.service.get_notifications(device_id=self.device_1.external_id)
        self.assertEqual(notifications[0].device_external_id, self.device_1.external_id)

    def test_process_defaults_to_now_plus_5s(self):
        notification = NotificationData(
            title="Hello",
            message="Is it me you're looking for?",
            link_source_id="see_it_in_your_eyes",
            device_ids=[self.device_1.external_id, self.device_2.external_id],
        )

        self.service.process(notification=notification)

        instance = ScheduledNotification.objects.filter(title=notification.title).get()
        self.assertEqual(
            instance.scheduled_for, timezone.now() + timezone.timedelta(seconds=5)
        )

    def test_send_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.service.send("anything")


class TestUnifiedNotificationService_ScheduledLike(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.device_1 = baker.make(Device, external_id="device_1")
        self.device_2 = baker.make(Device, external_id="device_2")
        self.notification_1 = baker.make(
            ScheduledNotification,
            identifier="notif_1",
            title="Test Notification 1",
            devices=[self.device_1, self.device_2],
        )
        self.notification_2 = baker.make(
            ScheduledNotification,
            identifier="notif_2",
            devices=[self.device_1],
        )
        self.service = UnifiedNotificationService()

    def test_get_all(self):
        notifications = self.service.get_all()
        self.assertEqual(len(notifications), 2)
        self.assertIn(self.notification_1, notifications)
        self.assertIn(self.notification_2, notifications)

    def test_get(self):
        notification = self.service.get("notif_1")
        self.assertEqual(notification, self.notification_1)

    def test_get_nonexistent(self):
        notification = self.service.get("nonexistent_notif")
        self.assertIsNone(notification)

    def test_delete(self):
        self.service.delete("notif_1")
        notifications = self.service.get_all()
        self.assertEqual(len(notifications), 1)
        self.assertNotIn(self.notification_1, notifications)
        self.assertIn(self.notification_2, notifications)

    def test_delete_nonexistent(self):
        self.service.delete("nonexistent_notif")
        notifications = self.service.get_all()
        self.assertEqual(len(notifications), 2)

    def test_upsert_insert(self):
        self.service.upsert(
            title="New Notification",
            body="This is a new notification.",
            scheduled_for="2024-07-01T10:00:00Z",
            identifier="notif_3",
            context={"type": "info", "module_slug": "notif"},
            device_ids=["device_1", "device_2", "device_3"],
            notification_type="info",
            module_slug="notif",
        )
        notifications = self.service.get_all()
        self.assertEqual(len(notifications), 3)
        new_notification = self.service.get("notif_3")
        self.assertEqual(new_notification.title, "New Notification")
        self.assertEqual(new_notification.devices.count(), 3)
        self.assertEqual(Device.objects.count(), 3)

    def test_upsert_update(self):
        instance = self.service.upsert(
            title="Updated Notification",
            body="This notification has been updated.",
            scheduled_for="2024-07-01T10:00:00Z",
            identifier="notif_1",
            context={"type": "info", "module_slug": "notif"},
            device_ids=["device_1", "device_2"],
            notification_type="info",
            module_slug="notif",
        )
        self.assertEqual(instance.pk, self.notification_1.pk)
        notifications = self.service.get_all()
        self.assertEqual(len(notifications), 2)
        notification = self.service.get("notif_1")
        self.assertEqual(notification.title, "Updated Notification")
        self.assertEqual(notification.devices.count(), 2)
        self.assertEqual(Device.objects.count(), 2)

    def test_upsert_invalid_expires_at(self):
        with self.assertRaises(NotificationServiceError):
            self.service.upsert(
                title="Invalid Notification",
                body="This notification has invalid expires_at.",
                scheduled_for="2024-07-01T10:00:00Z",
                identifier="notif_4",
                context={"type": "info", "module_slug": "notif"},
                device_ids=["device_1", "device_2"],
                notification_type="info",
                expires_at="2024-06-30T10:00:00Z",
                module_slug="notif",
            )

    def test_upsert_invalid_module_slug(self):
        with self.assertRaises(NotificationServiceError):
            self.service.upsert(
                title="Invalid Notification",
                body="This notification has invalid module_slug.",
                scheduled_for="2024-07-01T10:00:00Z",
                identifier="notif_5",
                context={"type": "info", "module_slug": "different_slug"},
                device_ids=["device_1", "device_2"],
                notification_type="info",
                module_slug="different_slug",
            )

    def test_upsert_empty_devices(self):
        notification = self.service.upsert(
            title="No Devices Notification",
            body="This notification has no devices.",
            scheduled_for="2024-07-01T10:00:00Z",
            identifier="notif_1",
            context={"type": "info", "module_slug": "notif"},
            device_ids=[],
            notification_type="info",
            module_slug="notif",
        )
        self.assertEqual(notification.devices.count(), 2)

    def test_upsert_new_and_existing_devices(self):
        self.service.upsert(
            title="Mixed Devices Notification",
            body="This notification has mixed devices.",
            scheduled_for="2024-07-01T10:00:00Z",
            identifier="notif_2",
            context={"type": "info", "module_slug": "notif"},
            device_ids=["device_2", "device_3"],
            notification_type="info",
            module_slug="notif",
        )
        notification = self.service.get("notif_2")
        self.assertEqual(notification.devices.count(), 3)
        self.assertEqual(Device.objects.count(), 3)

    def test_upsert_no_devices(self):
        with self.assertRaises(NotificationServiceError):
            self.service.upsert(
                title="No Devices Notification",
                body="This notification has no devices.",
                scheduled_for="2024-07-01T10:00:00Z",
                identifier="notif_1",
                context={"type": "info", "module_slug": "notif"},
                notification_type="info",
                module_slug="notif",
            )

    def test_upsert_all_devices(self):
        instance = self.service.upsert(
            title="All Devices Notification",
            body="This notification has all devices.",
            scheduled_for="2024-07-01T10:00:00Z",
            identifier="notif_1",
            context={"type": "info", "module_slug": "notif"},
            notification_type="info",
            module_slug="notif",
            send_all_devices=True,
        )
        self.assertEqual(instance.devices.count(), 2)

    def test_upsert_image_doesnt_exist(self):
        patched_image_service = Mock()
        patched_image_service.exists.return_value = False
        self.service.image_service = patched_image_service

        with self.assertRaises(NotificationServiceError):
            self.service.upsert(
                title="Notification",
                body="Body",
                scheduled_for="2024-07-01T10:00:00Z",
                identifier="notif_1",
                device_ids=["device_2"],
                context={"type": "info", "module_slug": "notif"},
                notification_type="info",
                image="image_str",
                module_slug="notif",
            )
