from django.utils import timezone
from model_bakery import baker

from city_pass.models import Notification, Session
from city_pass.services.notification import NotificationService
from core.tests.test_authentication import ResponsesActivatedAPITestCase
from notification.models.notification_models import Device, ScheduledNotification


class TestNotificationService(ResponsesActivatedAPITestCase):
    def setUp(self):
        for i in range(5):
            baker.make(Device, id=i + 1)

        session_1 = baker.make(Session, device_id_internal=1)
        session_2 = baker.make(Session, device_id_internal=2)
        baker.make(Session, device_id_internal=3)
        baker.make(Session, device_id_internal=4)
        baker.make(Session, device_id_internal=5)

        self.budget_1 = baker.make("Budget", code="budget1")
        self.budget_2 = baker.make("Budget", code="budget2")

        baker.make(
            "PassData", session=session_1, budgets=[self.budget_1, self.budget_2]
        )
        baker.make("PassData", session=session_2, budgets=[self.budget_1])

    def test_set_device_ids_all(self):
        notification = baker.make(Notification, budgets=[])
        service = NotificationService()

        device_ids = list(service.get_device_qs(notification))

        self.assertEqual(len(device_ids), 5)
        self.assertIn(1, device_ids)
        self.assertIn(2, device_ids)
        self.assertIn(3, device_ids)
        self.assertIn(4, device_ids)
        self.assertIn(5, device_ids)

    def test_set_device_ids_budgets(self):
        notification = baker.make(Notification, budgets=[self.budget_1, self.budget_2])
        service = NotificationService()

        device_ids = list(service.get_device_qs(notification))

        self.assertEqual(len(device_ids), 2)
        self.assertIn(1, device_ids)
        self.assertIn(2, device_ids)

    def test_call_everybody(self):
        notification = baker.make(Notification, budgets=[])
        service = NotificationService()

        service.send(notification)

        self.assertIsNotNone(notification.send_at)
        self.assertEqual(notification.nr_sessions, 5)
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

    def test_call_uses_existing_send_at_for_schedule(self):
        scheduled_for = timezone.now() + timezone.timedelta(days=1)
        notification = baker.make(
            Notification, budgets=[self.budget_1], send_at=scheduled_for
        )
        service = NotificationService()

        service.send(notification)

        scheduled_notification = ScheduledNotification.objects.get()
        self.assertEqual(
            scheduled_notification.identifier,
            service._create_identifier(notification.id),
        )
        self.assertEqual(scheduled_notification.scheduled_for, scheduled_for)
        self.assertEqual(notification.send_at, scheduled_for)
