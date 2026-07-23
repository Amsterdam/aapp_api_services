from django.utils import timezone
from model_bakery import baker
from rest_framework.test import APITestCase

from city_pass.models import Notification, Session
from city_pass.services.notification import NotificationService
from notification.models.notification_models import Device


class TestNotificationService(APITestCase):
    databases = {"default", "notification"}

    def setUp(self):
        for i in range(3):
            baker.make(Device, id=i + 1)
        session_1 = baker.make(Session, device_id_internal=1)
        session_2 = baker.make(Session, device_id_internal=2)
        baker.make(Session, device_id_internal=3)

        self.budget_1 = baker.make("Budget", code="budget1")
        self.budget_2 = baker.make("Budget", code="budget2")
        self.scheduled_for = timezone.now() + timezone.timedelta(days=1)

        baker.make(
            "PassData", session=session_1, budgets=[self.budget_1, self.budget_2]
        )
        baker.make("PassData", session=session_2, budgets=[self.budget_1])

    def test_call_everybody(self):
        notification = baker.make(
            Notification,
            budgets=[],
            send_at=self.scheduled_for,
        )
        service = NotificationService()

        service.send(notification)

        self.assertIsNotNone(notification.send_at)
        self.assertEqual(notification.nr_sessions, 3)

    def test_call_budget1(self):
        notification = baker.make(
            Notification,
            budgets=[self.budget_1],
            send_at=self.scheduled_for,
        )
        service = NotificationService()

        service.send(notification)

        self.assertIsNotNone(notification.send_at)
        self.assertEqual(notification.nr_sessions, 2)

    def test_call_budget2(self):
        notification = baker.make(
            Notification,
            budgets=[self.budget_2],
            send_at=self.scheduled_for,
        )
        service = NotificationService()

        service.send(notification)

        self.assertIsNotNone(notification.send_at)
        self.assertEqual(notification.nr_sessions, 1)

    def test_call_scheduled_notification(self):
        scheduled_for = timezone.now() + timezone.timedelta(hours=2)
        notification = baker.make(
            Notification, budgets=[self.budget_2], send_at=scheduled_for
        )
        service = NotificationService()

        service.send(notification)

        self.assertEqual(notification.send_at, scheduled_for)
