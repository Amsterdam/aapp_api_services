from datetime import datetime

from django.test import TestCase
from model_bakery import baker

from modules.models import Notification
from modules.services.notification import NotificationService


class TestScheduledNotificationService(TestCase):
    databases = ["default", "notification"]

    def setUp(self):
        super().setUp()
        self.notification_1 = baker.make(
            Notification,
            title="Title 1",
            message="unique message",
            send_at=datetime(2026, 4, 1, 10, 0, 0),
        )
        self.notification_2 = baker.make(Notification)
        self.service = NotificationService()

    def test_identifier(self):
        identifier = self.service._create_identifier()
        self.assertEqual(identifier.startswith(self.service.module_slug), True)

    def test_send_notification(self):
        self.service.send_notification(self.notification_1)

        self.assertEqual(
            Notification.objects.filter(title=self.notification_1.title).count(), 1
        )
