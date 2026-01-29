from model_bakery import baker

from core.services.scheduled_notification import (
    NotificationServiceError,
    ScheduledNotificationService,
)
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import Device, ScheduledNotification


class TestScheduledNotificationService(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.device_1 = baker.make(Device, external_id="device_1")
        self.device_2 = baker.make(Device, external_id="device_2")
        self.notification_1 = baker.make(
            ScheduledNotification,
            identifier="notif_1",
            devices=[self.device_1, self.device_2],
        )
        self.notification_2 = baker.make(
            ScheduledNotification, identifier="notif_2", devices=[self.device_1]
        )
        self.service = ScheduledNotificationService()

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
            context={},
            device_ids=["device_1", "device_2", "device_3"],
            notification_type="info",
            module_slug="notif",
        )
        notifications = self.service.get_all()
        self.assertEqual(len(notifications), 3)
        new_notification = self.service.get("notif_3")
        self.assertEqual(new_notification.title, "New Notification")
        self.assertEqual(new_notification.devices.count(), 3)
        self.assertEqual(Device.objects.count(), 3)  # One new device created

    def test_upsert_update(self):
        self.service.upsert(
            title="Updated Notification",
            body="This notification has been updated.",
            scheduled_for="2024-07-01T10:00:00Z",
            identifier="notif_1",
            context={},
            device_ids=["device_1", "device_2"],
            notification_type="info",
        )
        notifications = self.service.get_all()
        self.assertEqual(len(notifications), 2)
        notification = self.service.get("notif_1")
        self.assertEqual(notification.title, "Updated Notification")
        self.assertEqual(notification.devices.count(), 2)
        self.assertEqual(Device.objects.count(), 2)  # No new devices created

    def test_upsert_invalid_expires_at(self):
        with self.assertRaises(NotificationServiceError):
            self.service.upsert(
                title="Invalid Notification",
                body="This notification has invalid expires_at.",
                scheduled_for="2024-07-01T10:00:00Z",
                identifier="notif_4",
                context={},
                device_ids=["device_1", "device_2"],
                notification_type="info",
                expires_at="2024-06-30T10:00:00Z",
            )

    def test_upsert_invalid_module_slug(self):
        with self.assertRaises(NotificationServiceError):
            self.service.upsert(
                title="Invalid Notification",
                body="This notification has invalid module_slug.",
                scheduled_for="2024-07-01T10:00:00Z",
                identifier="notif_5",
                context={},
                device_ids=["device_1", "device_2"],
                notification_type="info",
                module_slug="different_slug",
            )

    def test_upsert_no_devices(self):
        notification = self.service.upsert(
            title="No Devices Notification",
            body="This notification has no devices.",
            scheduled_for="2024-07-01T10:00:00Z",
            identifier="notif_1",
            context={},
            device_ids=[],
            notification_type="info",
        )
        self.assertEqual(notification.devices.count(), 2)  # Original devices remain

    def test_upsert_new_and_existing_devices(self):
        self.service.upsert(
            title="Mixed Devices Notification",
            body="This notification has mixed devices.",
            scheduled_for="2024-07-01T10:00:00Z",
            identifier="notif_2",
            context={},
            device_ids=["device_2", "device_3"],
            notification_type="info",
        )
        notification = self.service.get("notif_2")
        self.assertEqual(notification.devices.count(), 3)
        self.assertEqual(Device.objects.count(), 3)  # One new device created
