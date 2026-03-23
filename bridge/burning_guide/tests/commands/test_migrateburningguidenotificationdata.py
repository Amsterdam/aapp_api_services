from datetime import datetime

from django.core.management import call_command
from django.test import TestCase
from model_bakery import baker

from bridge.models import BurningGuideNotification
from notification.models import BurningGuideDevice


class BurningGuideMigrationTest(TestCase):
    databases = {"default", "notification"}

    def test_migrate_burning_guide_notification_data(self):
        schedule_1 = baker.make(
            BurningGuideNotification,
            postal_code="1023",
            device_id="device_1",
            send_at=None,
        )
        call_command("migrateburningguidenotificationdata")

        burning_guide_notifications = BurningGuideDevice.objects.all()
        self.assertEqual(burning_guide_notifications.count(), 1)

        burning_guide_notification = burning_guide_notifications.first()
        self.assertEqual(burning_guide_notification.device_id, schedule_1.device_id)
        self.assertEqual(
            burning_guide_notification.postal_code,
            schedule_1.postal_code,
        )
        # not checking created_at as it is auto_now_add, but checking that send_at is None as in the schedule
        self.assertEqual(burning_guide_notification.send_at, schedule_1.send_at)

    def test_migrate_burning_guide_notification_data_with_record_already_existing(self):
        already_existing = baker.make(
            BurningGuideDevice,
            device_id="device_1",
            postal_code="1023",
            send_at=None,
        )
        baker.make(
            BurningGuideNotification,
            postal_code="2345",
            device_id="device_1",
            send_at=datetime(2024, 1, 1, 12, 0, 0),
        )
        call_command("migrateburningguidenotificationdata")

        burning_guide_notifications = BurningGuideDevice.objects.all()
        self.assertEqual(burning_guide_notifications.count(), 1)

        # check that info is unchanged for already existing record
        burning_guide_notification = burning_guide_notifications.first()
        self.assertEqual(burning_guide_notification.send_at, already_existing.send_at)
        self.assertEqual(
            burning_guide_notification.postal_code,
            already_existing.postal_code,
        )

        # check that old records are deleted after migration
        self.assertEqual(BurningGuideNotification.objects.count(), 0)
