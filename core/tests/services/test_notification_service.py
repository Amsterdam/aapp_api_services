import datetime

from django.utils import timezone
from freezegun import freeze_time
from model_bakery import baker

from core.services.notification_service import (
    AbstractNotificationService,
    NotificationData,
)
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import (
    Device,
    Notification,
    NotificationLast,
    ScheduledNotification,
)


@freeze_time("2026-02-01 10:00:00")
class TestScheduledAbstractNotificationService(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.module_slug = "test-slug"
        self.service = AbstractNotificationService()
        self.service.module_slug = self.module_slug
        self.service.notification_type = "test-slug:notification"
        self.device_1 = baker.make(Device, external_id="device_1")
        self.device_2 = baker.make(Device, external_id="device_2")
        self.notification_last_1 = baker.make(
            NotificationLast,
            device=self.device_1,
            module_slug=self.module_slug,
            notification_scope=f"{self.module_slug}:default",
        )
        self.notification = baker.make(
            Notification,
            device=self.device_1,
        )

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

    def test_process(self):

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

        notification = NotificationData(
            title="Hello",
            message="I've just got to let you know",
            link_source_id="wonder_where_you_are",
            device_ids=[self.device_1.external_id, self.device_2.external_id],
        )

        with self.assertRaises(NotImplementedError):
            self.service.send(notification)
