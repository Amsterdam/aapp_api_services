from datetime import datetime

from django.contrib.auth.models import User
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
        self.user = baker.make(User, username="testuser")

    def test_identifier(self):
        identifier = self.service._create_identifier(
            created_at=self.notification_1.created_at, created_by=self.user
        )
        self.assertEqual(identifier.startswith(self.service.module_slug), True)
        self.assertEqual(
            self.notification_1.created_at.strftime("%Y%m%d%H%M%S") in identifier, True
        )

    def test_upsert_scheduled_notification(self):
        self.service.upsert_scheduled_notification(self.notification_1)

        self.assertEqual(
            Notification.objects.filter(title=self.notification_1.title).count(), 1
        )
