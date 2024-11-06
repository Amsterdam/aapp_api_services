from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings

from notification.models import Client, Notification
from notification.services.push import PushService, PushServiceClientLimitError
from notification.utils.test_utils import MockFirebaseSendEach, apply_firebase_patches


class TestPushService(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.applied_patches = apply_firebase_patches(cls)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        for p in cls.applied_patches:
            p.stop()

    def create_unsaved_notification(self):
        notification = Notification(
            title="foobar title",
            body="foobar body",
            module_slug="foobar-slug",
            context={"some": "context"},
            created_at="2024-10-31T16:30",
        )
        return notification

    def create_client(self):
        client = Client(
            external_id="abc", firebase_token="abc_token", receive_push=True
        )
        client.save()
        return client

    def create_clients(self, amount: int, with_token=True):
        new_clients = []
        mock_token = None
        if with_token:
            mock_token = "abc_token"

        for i in range(amount):
            client = Client(
                external_id=f"abc_{i}", firebase_token=mock_token, receive_push=True
            )
            client.save()
            new_clients.append(client)
        return new_clients

    @patch(
        "notification.services.push.messaging.send_each",
    )
    def test_push_success(self, multicast_mock):
        multicast_mock.return_value = MockFirebaseSendEach(5)

        notification = self.create_unsaved_notification()
        client = self.create_client()

        push_service = PushService(notification, [client.external_id])
        push_service.push()

        notification = Notification.objects.filter(client_id=client.external_id).first()
        self.assertIsNotNone(notification.pushed_at)

    @patch(
        "notification.services.push.messaging.send_each",
    )
    def test_push_with_some_failed_tokens(self, multicast_mock):
        client_count = 5
        failed_client_count = 2

        multicast_mock.return_value = MockFirebaseSendEach(
            client_count, fail_count=failed_client_count
        )

        notification = self.create_unsaved_notification()
        clients = self.create_clients(client_count)

        push_service = PushService(notification, [c.external_id for c in clients])

        with self.assertLogs("notification.services.push", level="ERROR") as cm:
            notification = push_service.push()

        self.assertEqual(len(cm.output), failed_client_count)
        for output in cm.output:
            self.assertIn("Failed to send notification to client", output)

    @override_settings(FIREBASE_CLIENT_LIMIT=5)
    def test_hit_max_clients(self):
        client_ids = [f"client_{i}" for i in range(settings.FIREBASE_CLIENT_LIMIT + 1)]

        with self.assertRaises(PushServiceClientLimitError):
            PushService(None, client_ids)

    def test_client_without_firebase_tokens(self):
        notification = self.create_unsaved_notification()
        clients = self.create_clients(5, with_token=False)

        push_service = PushService(notification, [c.external_id for c in clients])

        with self.assertLogs("notification.services.push", level="INFO") as cm:
            push_service.push()

        # For each client a notification should have been created
        for c in clients:
            notification = Notification.objects.filter(client_id=c.external_id).first()
            self.assertIsNotNone(notification)

        for output in cm.output:
            self.assertIn("none of the clients have a Firebase token", output)
