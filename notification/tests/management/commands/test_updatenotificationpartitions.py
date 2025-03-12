import datetime

from django.core.management import call_command
from django.test import TransactionTestCase
from freezegun import freeze_time
from model_bakery import baker

from notification.management.commands.updatenotificationpartitions import DAYS_TO_KEEP
from notification.models import Notification, ScheduledNotification


class UpdatePartitionsTest(TransactionTestCase):
    def test_old_notifications_are_deleted(self):
        initial_date = datetime.date.today()
        baker.make(
            Notification,
            _quantity=4,
            created_at=initial_date,
        )

        # Advance time beyond DAYS_TO_KEEP
        later_date = initial_date + datetime.timedelta(days=DAYS_TO_KEEP + 1)
        with freeze_time(later_date):
            call_command("updatenotificationpartitions")

            # Assert only the more recent notifications remain
            remaining_notifications = Notification.objects.all()
            self.assertEqual(remaining_notifications.count(), 0)

    def test_some_notifications_are_deleted(self):
        initial_date = datetime.date.today()
        baker.make(
            Notification,
            _quantity=4,
            created_at=initial_date,
        )
        more_recent_notification_date = initial_date + datetime.timedelta(days=3)
        recent_notifications = baker.make(
            Notification,
            _quantity=6,
            created_at=more_recent_notification_date,
        )

        # Advance time beyond DAYS_TO_KEEP
        later_date = initial_date + datetime.timedelta(days=DAYS_TO_KEEP + 1)
        with freeze_time(later_date):
            call_command("updatenotificationpartitions")

            # Assert only the more recent notifications remain
            remaining_notifications = Notification.objects.all()
            self.assertEqual(remaining_notifications.count(), 6)
            for notification in remaining_notifications:
                self.assertIn(notification.id, [n.id for n in recent_notifications])

    def test_no_notifications_deleted_within_days_to_keep(self):
        initial_date = datetime.date.today()
        baker.make(
            Notification,
            _quantity=5,
            created_at=initial_date,
        )

        later_date = initial_date + datetime.timedelta(days=DAYS_TO_KEEP - 1)
        with freeze_time(later_date):
            call_command("updatenotificationpartitions")

        remaining_notifications = Notification.objects.all()
        self.assertEqual(remaining_notifications.count(), 5)

    def test_scheduled_notifications_are_deleted(self):
        initial_date = datetime.datetime.now()
        baker.make(
            ScheduledNotification,
            _quantity=6,
            pushed_at=initial_date,
        )
        more_recent_notification_date = initial_date + datetime.timedelta(days=3)
        recent_notifications = baker.make(
            ScheduledNotification,
            _quantity=2,
            pushed_at=more_recent_notification_date,
        )
        unpushed_notifications = baker.make(
            ScheduledNotification,
            _quantity=3,
            pushed_at=None,
        )

        # Advance time beyond DAYS_TO_KEEP
        later_date = initial_date + datetime.timedelta(days=DAYS_TO_KEEP + 1)
        with freeze_time(later_date):
            call_command("updatenotificationpartitions")

            # Assert only the more recent notifications remain
            remaining_scheduled_notifications = ScheduledNotification.objects.all()
            self.assertEqual(remaining_scheduled_notifications.count(), 5)
            for notification in remaining_scheduled_notifications:
                self.assertIn(
                    notification.id,
                    [n.id for n in recent_notifications + unpushed_notifications],
                )
