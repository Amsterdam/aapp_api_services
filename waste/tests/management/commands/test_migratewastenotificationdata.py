from datetime import datetime

from django.core.management import call_command
from django.test import TestCase
from model_bakery import baker

from notification.models import WasteNotification
from waste.models import NotificationSchedule


class WasteMigrationTest(TestCase):
    databases = {"default", "notification"}

    def test_migrate_waste_notification_data(self):
        schedule_1 = baker.make(
            NotificationSchedule,
            bag_nummeraanduiding_id="12345",
            device_id="device_1",
            updated_at=None,
        )
        call_command("migratewastenotificationdata")

        waste_notifications = WasteNotification.objects.all()
        self.assertEqual(waste_notifications.count(), 1)

        waste_notification = waste_notifications.first()
        self.assertEqual(waste_notification.device_id, schedule_1.device_id)
        self.assertEqual(
            waste_notification.bag_nummeraanduiding_id,
            schedule_1.bag_nummeraanduiding_id,
        )
        # not checking created_at as it is auto_now_add, but checking that updated_at is None as in the schedule
        self.assertEqual(waste_notification.updated_at, schedule_1.updated_at)

    def test_migrate_waste_notification_data_with_record_already_existing(self):
        already_existing = baker.make(
            WasteNotification,
            device_id="device_1",
            bag_nummeraanduiding_id="12345",
            updated_at=None,
        )
        baker.make(
            NotificationSchedule,
            bag_nummeraanduiding_id="2345",
            device_id="device_1",
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        call_command("migratewastenotificationdata")

        waste_notifications = WasteNotification.objects.all()
        self.assertEqual(waste_notifications.count(), 1)

        # check that info is unchanged for already existing record
        waste_notification = waste_notifications.first()
        self.assertEqual(waste_notification.updated_at, already_existing.updated_at)
        self.assertEqual(
            waste_notification.bag_nummeraanduiding_id,
            already_existing.bag_nummeraanduiding_id,
        )

        # check that old records are deleted after migration
        self.assertEqual(NotificationSchedule.objects.count(), 0)
