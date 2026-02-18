from model_bakery import baker
from rest_framework.test import APITestCase

from city_pass.models import Notification, Session
from city_pass.services.notification import NotificationService


class TestNotificationService(APITestCase):
    databases = {"default", "notification"}

    def setUp(self):
        session_1 = baker.make(Session, device_id="device1")
        session_2 = baker.make(Session, device_id="device2")
        baker.make(Session, device_id="device3")

        self.budget_1 = baker.make("Budget", code="budget1")
        self.budget_2 = baker.make("Budget", code="budget2")

        baker.make(
            "PassData", session=session_1, budgets=[self.budget_1, self.budget_2]
        )
        baker.make("PassData", session=session_2, budgets=[self.budget_1])

    def test_call_everybody(self):
        notification = baker.make(Notification, budgets=[])
        service = NotificationService()

        service.send(notification)

        self.assertIsNotNone(notification.send_at)
        self.assertEqual(notification.nr_sessions, 3)

    def test_call_budget1(self):
        notification = baker.make(Notification, budgets=[self.budget_1])
        service = NotificationService()

        service.send(notification)

        self.assertIsNotNone(notification.send_at)
        self.assertEqual(notification.nr_sessions, 2)

    def test_call_budget2(self):
        notification = baker.make(Notification, budgets=[self.budget_2])
        service = NotificationService()

        service.send(notification)

        self.assertIsNotNone(notification.send_at)
        self.assertEqual(notification.nr_sessions, 1)
