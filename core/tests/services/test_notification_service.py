import datetime
from unittest.mock import Mock

from django.utils import timezone
from freezegun import freeze_time
from model_bakery import baker

from core.services.notification_service import (
    NotificationData,
    NotificationServiceAbstract,
    NotificationServiceError,
)
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import (
    Device,
    Notification,
    NotificationLast,
    ScheduledNotification,
)


class MockUnifiedNotificationService(NotificationServiceAbstract):
    module_slug = "test-slug"
    notification_type = "test-slug:notification"


@freeze_time("2026-02-01 10:00:00")
class TestNotificationService_Unscheduled(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.module_slug = "test-slug"
        self.service = MockUnifiedNotificationService()
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
        notifications = self.service.get_notifications(
            device_id=self.device_1.external_id
        )
        self.assertEqual(notifications[0].device_external_id, self.device_1.external_id)

    def test_upsert_defaults_to_now_plus_5s(self):
        notification = NotificationData(
            title="Hello",
            message="Is it me you're looking for?",
            link_source_id="see_it_in_your_eyes",
            device_ids=[self.device_1.external_id, self.device_2.external_id],
        )

        self.service.upsert(notification=notification)

        instance = ScheduledNotification.objects.filter(title=notification.title).get()
        self.assertEqual(
            instance.scheduled_for, timezone.now() + timezone.timedelta(seconds=5)
        )

    def test_send_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.service.send("anything")


class TestNotificationService_Scheduled(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.service = MockUnifiedNotificationService()
        self.device_1 = baker.make(Device, external_id="device_1")
        self.device_2 = baker.make(Device, external_id="device_2")
        self.notification_1 = baker.make(
            ScheduledNotification,
            identifier=f"{self.service.module_slug}:notif_1",
            title="Test Notification 1",
            devices=[self.device_1, self.device_2],
        )
        self.notification_2 = baker.make(
            ScheduledNotification,
            identifier=f"{self.service.module_slug}:notif_2",
            devices=[self.device_1],
        )

    def test_get_all(self):
        notifications = self.service.get_all_scheduled_notifications()
        self.assertEqual(len(notifications), 2)
        self.assertIn(self.notification_1, notifications)
        self.assertIn(self.notification_2, notifications)

    def test_get(self):
        notification = self.service.get_scheduled_notification(
            f"{self.service.module_slug}:notif_1"
        )
        self.assertEqual(notification, self.notification_1)

    def test_get_nonexistent(self):
        notification = self.service.get_scheduled_notification(
            f"{self.service.module_slug}:nonexistent_notif"
        )
        self.assertIsNone(notification)

    def test_delete(self):
        self.service.delete_scheduled_notification(
            f"{self.service.module_slug}:notif_1"
        )
        notifications = self.service.get_all_scheduled_notifications()
        self.assertEqual(len(notifications), 1)
        self.assertNotIn(self.notification_1, notifications)
        self.assertIn(self.notification_2, notifications)

    def test_delete_nonexistent(self):
        self.service.delete_scheduled_notification(
            f"{self.service.module_slug}:nonexistent_notif"
        )
        notifications = self.service.get_all_scheduled_notifications()
        self.assertEqual(len(notifications), 2)

    def test_upsert_insert(self):
        notification = NotificationData(
            title="Hello",
            message="Is it me you're looking for?",
            link_source_id="see_it_in_your_eyes",
            device_ids=[self.device_1.external_id, self.device_2.external_id],
        )
        self.service.upsert(
            notification=notification,
            scheduled_for=timezone.now(),
            identifier=f"{self.service.module_slug}:notif_3",
            context={
                "type": self.service.notification_type,
                "module_slug": self.service.module_slug,
            },
        )
        notifications = self.service.get_all_scheduled_notifications()
        self.assertEqual(len(notifications), 3)
        new_notification = self.service.get_scheduled_notification(
            f"{self.service.module_slug}:notif_3"
        )
        self.assertEqual(new_notification.title, "Hello")
        self.assertEqual(new_notification.devices.count(), 2)
        self.assertEqual(Device.objects.count(), 2)

    def test_upsert_update(self):
        notification = NotificationData(
            title="Updated Notification",
            message="This notification has been updated.",
            link_source_id="see_it_in_your_eyes",
            device_ids=[self.device_1.external_id, self.device_2.external_id],
        )
        instance = self.service.upsert(
            notification=notification,
            scheduled_for=timezone.now(),
            identifier=f"{self.service.module_slug}:notif_1",
            context={
                "type": self.service.notification_type,
                "module_slug": self.service.module_slug,
            },
        )
        self.assertEqual(instance.pk, self.notification_1.pk)
        notifications = self.service.get_all_scheduled_notifications()
        self.assertEqual(len(notifications), 2)
        notification = self.service.get_scheduled_notification(
            f"{self.service.module_slug}:notif_1"
        )
        self.assertEqual(notification.title, "Updated Notification")
        self.assertEqual(notification.devices.count(), 2)
        self.assertEqual(Device.objects.count(), 2)

    def test_upsert_invalid_expires_at(self):
        with self.assertRaises(NotificationServiceError):
            notification = NotificationData(
                title="Invalid Notification",
                message="This notification has invalid expires_at.",
                link_source_id="see_it_in_your_eyes",
                device_ids=[self.device_1.external_id, self.device_2.external_id],
            )
            self.service.upsert(
                notification=notification,
                scheduled_for=timezone.now(),
                identifier=f"{self.service.module_slug}:notif_4",
                context={
                    "type": self.service.notification_type,
                    "module_slug": self.service.module_slug,
                },
                expires_at=timezone.now() - timezone.timedelta(minutes=30),
            )

    def test_upsert_invalid_identifier(self):
        with self.assertRaises(NotificationServiceError):
            notification = NotificationData(
                title="Invalid Notification",
                message="This notification has invalid identifier.",
                link_source_id="abc",
                device_ids=[self.device_1.external_id, self.device_2.external_id],
            )
            self.service.upsert(
                notification=notification,
                scheduled_for=timezone.now(),
                identifier="different_slug:notif_5",
                context={
                    "type": self.service.notification_type,
                    "module_slug": "different_slug",
                },
            )

    def test_upsert_empty_devices(self):
        notification = NotificationData(
            title="No Devices Notification",
            message="This notification has no devices.",
            link_source_id="abc",
            device_ids=[],
        )
        notification = self.service.upsert(
            notification=notification,
            scheduled_for=timezone.now(),
            identifier=f"{self.service.module_slug}:notif_1",
            context={
                "type": self.service.notification_type,
                "module_slug": self.service.module_slug,
            },
        )
        self.assertEqual(notification.devices.count(), 2)

    def test_upsert_new_and_existing_devices(self):
        notification = NotificationData(
            title="Mixed Devices Notification",
            message="This notification has mixed devices.",
            link_source_id="abc",
            device_ids=["device_2", "device_3"],
        )
        self.service.upsert(
            notification=notification,
            scheduled_for=timezone.now(),
            identifier=f"{self.service.module_slug}:notif_2",
            context={
                "type": self.service.notification_type,
                "module_slug": self.service.module_slug,
            },
        )
        notification = self.service.get_scheduled_notification(
            f"{self.service.module_slug}:notif_2"
        )
        self.assertEqual(notification.devices.count(), 3)
        self.assertEqual(Device.objects.count(), 3)

    def test_upsert_no_devices(self):
        notification = NotificationData(
            title="No Devices Notification",
            message="This notification has no devices.",
            link_source_id="abc",
        )
        with self.assertRaises(NotificationServiceError):
            self.service.upsert(
                notification=notification,
                scheduled_for=timezone.now(),
                identifier=f"{self.service.module_slug}:notif_1",
                context={
                    "type": self.service.notification_type,
                    "module_slug": self.service.module_slug,
                },
            )

    def test_upsert_all_devices(self):
        notification = NotificationData(
            title="All Devices Notification",
            message="This notification has all devices.",
            link_source_id="abc",
        )
        instance = self.service.upsert(
            notification=notification,
            scheduled_for=timezone.now(),
            identifier=f"{self.service.module_slug}:notif_1",
            context={
                "type": self.service.notification_type,
                "module_slug": self.service.module_slug,
            },
            send_all_devices=True,
        )
        self.assertEqual(instance.devices.count(), 2)

    def test_upsert_image_doesnt_exist(self):
        patched_image_service = Mock()
        patched_image_service.exists.return_value = False
        self.service.image_service = patched_image_service

        notification = NotificationData(
            title="Notification",
            message="Body",
            link_source_id="abc",
            device_ids=["device_2"],
            image_set_id=1,
        )

        with self.assertRaises(NotificationServiceError):
            self.service.upsert(
                notification=notification,
                scheduled_for=timezone.now(),
                identifier=f"{self.service.module_slug}:notif_1",
                context={
                    "type": self.service.notification_type,
                    "module_slug": self.service.module_slug,
                },
            )
