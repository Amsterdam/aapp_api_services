from datetime import datetime, timedelta

from django.core.management import call_command
from django.test import TransactionTestCase, override_settings
from model_bakery import baker

from notification.models import Device, Notification, ScheduledNotification
from notification.utils.patch_utils import apply_init_firebase_patches


class UpdateScheduledNotificationsTest(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.firebase_paths = apply_init_firebase_patches()

    def test_push_scheduled_notification(self):
        scheduled_date = datetime.now() - timedelta(days=1)
        devices = baker.make(Device, _quantity=2)
        baker.make(
            ScheduledNotification,
            scheduled_for=scheduled_date,
            devices=devices,
            is_ready=True,
        )

        call_command("pushschedulednotifications", "--test-mode")

        self.assertEqual(ScheduledNotification.objects.count(), 0)
        self.assertEqual(Notification.objects.count(), 2)

    def test_push_no_scheduled_notification(self):
        scheduled_date_future = datetime.now() + timedelta(days=1)
        devices = baker.make(Device, _quantity=2)
        baker.make(
            ScheduledNotification,
            scheduled_for=scheduled_date_future,
            devices=devices,
            is_ready=True,
        )

        call_command("pushschedulednotifications", "--test-mode")

        self.assertEqual(ScheduledNotification.objects.count(), 1)
        self.assertEqual(Notification.objects.count(), 0)

    def test_push_some_scheduled_notification_complex(self):
        date_in_past = datetime.now() - timedelta(days=2)
        date_in_future = datetime.now() + timedelta(days=1)
        devices = baker.make(Device, _quantity=5)
        baker.make(
            ScheduledNotification,
            scheduled_for=date_in_past,
            devices=devices,
            is_ready=True,
        )
        devices = baker.make(Device, _quantity=2)
        baker.make(
            ScheduledNotification,
            scheduled_for=date_in_future,
            devices=devices,
            is_ready=True,
        )

        call_command("pushschedulednotifications", "--test-mode")

        self.assertEqual(ScheduledNotification.objects.count(), 1)
        self.assertEqual(Notification.objects.count(), 5)

    def test_push_expired_scheduled_notification(self):
        devices = baker.make(Device, _quantity=2)
        yesterday = datetime.now() - timedelta(days=1)
        tomorrow = datetime.now() + timedelta(days=1)

        # non_expirable_notification
        baker.make(
            ScheduledNotification,
            scheduled_for=yesterday,
            devices=devices,
            is_ready=True,
        )

        # expirable_notification
        baker.make(
            ScheduledNotification,
            scheduled_for=yesterday,
            expires_at=yesterday + timedelta(minutes=10),
            devices=devices,
            is_ready=True,
        )

        future_notification = baker.make(
            ScheduledNotification,
            scheduled_for=tomorrow,
            expires_at=tomorrow + timedelta(minutes=10),
            devices=devices,
            is_ready=True,
        )
        call_command("pushschedulednotifications", "--test-mode")

        not_pushed_notifications = ScheduledNotification.objects.all()
        self.assertTrue(future_notification in not_pushed_notifications)

        self.assertEqual(Notification.objects.count(), len(devices))

    @override_settings(NOTIFICATION_DEVICE_BATCH_SIZE=7)
    def test_process_notifications_in_batches(self):
        nr_devices = 50
        devices = baker.make(Device, _quantity=nr_devices)
        baker.make(
            ScheduledNotification,
            scheduled_for=datetime.now() - timedelta(minutes=1),
            devices=devices,
            is_ready=True,
        )

        call_command("pushschedulednotifications", "--test-mode")

        self.assertEqual(ScheduledNotification.objects.count(), 0)
        self.assertEqual(Notification.objects.count(), nr_devices)
        for device in devices:
            self.assertEqual(Notification.objects.filter(device=device).count(), 1)
