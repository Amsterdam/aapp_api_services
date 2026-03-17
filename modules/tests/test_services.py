from datetime import datetime

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
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
        self.notification_2 = baker.make(
            Notification,
            send_at=datetime(2026, 4, 1, 10, 0, 0),
        )
        self.service = NotificationService()
        self.user = baker.make(User, username="testuser")

    def test_identifier(self):
        identifier = self.service._create_identifier(123)
        self.assertEqual(identifier.startswith(self.service.module_slug), True)
        self.assertIn("123", identifier)

    def test_send_notification(self):
        self.service.send(self.notification_1)

        self.assertEqual(
            Notification.objects.filter(title=self.notification_1.title).count(), 1
        )

    def test_send_notification_with_url(self):
        self.notification_2.url = "https://example.com"
        self.service.send(self.notification_2)

        self.assertEqual(
            Notification.objects.filter(title=self.notification_2.title).count(), 1
        )

    def test_send_notification_with_deeplink(self):
        self.notification_3 = baker.make(
            Notification,
            send_at=datetime(2026, 4, 1, 10, 0, 0),
        )
        self.notification_3.deeplink = "app://example"
        self.service.send(self.notification_3)

        self.assertEqual(
            Notification.objects.filter(title=self.notification_3.title).count(), 1
        )

    def test_send_notification_with_url_and_deeplink(self):
        self.notification_2.url = "https://example.com"
        self.notification_2.deeplink = "app://example"
        with self.assertRaises(ValidationError):
            self.service.send(self.notification_2)
