from datetime import datetime, timedelta

from django.core.management import call_command
from django.test import TransactionTestCase
from model_bakery import baker

from notification.models import Device, Notification, ScheduledNotification


class UpdateScheduledNotificationsTest(TransactionTestCase):
    def test_push_scheduled_notification(self):
        scheduled_date = datetime.now() - timedelta(days=1)
        devices = baker.make(Device, _quantity=2)
        baker.make(
            ScheduledNotification,
            scheduled_for=scheduled_date,
            pushed_at=None,
            devices=devices,
        )

        call_command("pushschedulednotifications")

        self.assertEqual(
            ScheduledNotification.objects.filter(pushed_at__isnull=False).count(), 1
        )
        self.assertEqual(Notification.objects.count(), 2)

    def test_push_no_scheduled_notification(self):
        scheduled_date = datetime.now() + timedelta(days=1)
        devices = baker.make(Device, _quantity=2)
        baker.make(
            ScheduledNotification,
            scheduled_for=scheduled_date,
            pushed_at=None,
            devices=devices,
        )

        call_command("pushschedulednotifications")

        self.assertEqual(
            ScheduledNotification.objects.filter(pushed_at__isnull=False).count(), 0
        )
        self.assertEqual(Notification.objects.count(), 0)

    def test_push_do_not_resend_scheduled_notification(self):
        scheduled_date = datetime.now() - timedelta(days=1)
        devices = baker.make(Device, _quantity=2)
        baker.make(
            ScheduledNotification,
            scheduled_for=scheduled_date,
            pushed_at=scheduled_date,
            devices=devices,
        )

        call_command("pushschedulednotifications")

        self.assertEqual(
            ScheduledNotification.objects.filter(pushed_at__isnull=False).count(), 1
        )
        self.assertEqual(Notification.objects.count(), 0)

    def test_push_some_scheduled_notification_complex(self):
        date_1 = datetime.now() - timedelta(days=2)
        date_2 = datetime.now() - timedelta(days=1)
        date_3 = datetime.now() + timedelta(days=1)
        devices = baker.make(Device, _quantity=3)
        baker.make(
            ScheduledNotification,
            scheduled_for=date_1,
            pushed_at=date_2,
            devices=devices,
        )
        devices = baker.make(Device, _quantity=5)
        baker.make(
            ScheduledNotification, scheduled_for=date_2, pushed_at=None, devices=devices
        )
        devices = baker.make(Device, _quantity=2)
        baker.make(
            ScheduledNotification, scheduled_for=date_3, pushed_at=None, devices=devices
        )

        call_command("pushschedulednotifications")

        self.assertEqual(
            ScheduledNotification.objects.filter(pushed_at__isnull=False).count(), 2
        )
        self.assertEqual(Notification.objects.count(), 5)

    def test_push_expired_scheduled_notification(self):
        devices = baker.make(Device, _quantity=2)
        yesterday = datetime.now() - timedelta(days=1)
        tomorrow = datetime.now() + timedelta(days=1)

        non_expirable_notification = baker.make(
            ScheduledNotification,
            scheduled_for=yesterday,
            pushed_at=None,
            devices=devices,
        )

        expirable_notification = baker.make(
            ScheduledNotification,
            scheduled_for=yesterday,
            expires_at=yesterday + timedelta(minutes=10),
            pushed_at=None,
            devices=devices,
        )

        future_notification = baker.make(
            ScheduledNotification,
            scheduled_for=tomorrow,
            expires_at=tomorrow + timedelta(minutes=10),
            pushed_at=None,
            devices=devices,
        )

        call_command("pushschedulednotifications")

        pushed_notifications = ScheduledNotification.objects.filter(
            pushed_at__lt="3000-01-01 00:00:00"
        )
        not_pushed_notifications = ScheduledNotification.objects.filter(
            pushed_at__isnull=True
        )
        expired_notifications = ScheduledNotification.objects.filter(
            pushed_at="3000-01-01 00:00:00"
        )
        self.assertTrue(non_expirable_notification in pushed_notifications)
        self.assertTrue(expirable_notification in expired_notifications)
        self.assertTrue(future_notification in not_pushed_notifications)

        self.assertEqual(Notification.objects.count(), len(devices))
