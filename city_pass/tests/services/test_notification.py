from model_bakery import baker

from city_pass.models import Notification, Session
from city_pass.services.notification import NotificationService
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models import ScheduledNotification


class TestNotificationService(ResponsesActivatedAPITestCase):
    def setUp(self):
        session_1 = baker.make(Session, device_id="device1")
        session_2 = baker.make(Session, device_id="device2")
        baker.make(Session, device_id="device3")
        baker.make(Session, device_id=None)  # Session without device_id
        baker.make(Session, device_id=None)  # Session without device_id

        self.budget_1 = baker.make("Budget", code="budget1")
        self.budget_2 = baker.make("Budget", code="budget2")

        baker.make(
            "PassData", session=session_1, budgets=[self.budget_1, self.budget_2]
        )
        baker.make("PassData", session=session_2, budgets=[self.budget_1])

    def test_set_device_ids_all(self):
        notification = baker.make(Notification, budgets=[])
        service = NotificationService()

        device_ids = service.get_device_ids(notification)

        self.assertEqual(len(device_ids), 3)
        self.assertIn("device1", device_ids)
        self.assertIn("device2", device_ids)
        self.assertIn("device3", device_ids)

    def test_set_device_ids_budgets(self):
        notification = baker.make(Notification, budgets=[self.budget_1, self.budget_2])
        service = NotificationService()

        device_ids = service.get_device_ids(notification)

        self.assertEqual(len(device_ids), 2)
        self.assertIn("device1", device_ids)
        self.assertIn("device2", device_ids)

    def test_call_everybody(self):
        notification = baker.make(Notification, budgets=[])
        service = NotificationService()

        service.send(notification)

        self.assertIsNotNone(notification.send_at)
        self.assertEqual(notification.nr_sessions, 3)
        self.assertEqual(ScheduledNotification.objects.count(), 1)

    def test_call_budget1(self):
        notification = baker.make(Notification, budgets=[self.budget_1])
        service = NotificationService()

        service.send(notification)

        self.assertIsNotNone(notification.send_at)
        self.assertEqual(notification.nr_sessions, 2)
        self.assertEqual(ScheduledNotification.objects.count(), 1)

    def test_call_budget2(self):
        notification = baker.make(Notification, budgets=[self.budget_2])
        service = NotificationService()

        service.send(notification)

        self.assertIsNotNone(notification.send_at)
        self.assertEqual(notification.nr_sessions, 1)
        self.assertEqual(ScheduledNotification.objects.count(), 1)

    def test_call_with_image(self):
        notification = baker.make(
            Notification,
            budgets=[self.budget_2],
            image_set_id=1,
        )
        service = NotificationService()

        service.send(notification)

        self.assertIsNotNone(notification.send_at)
        self.assertEqual(notification.nr_sessions, 1)
        self.assertEqual(ScheduledNotification.objects.count(), 1)
