import json
from unittest.mock import patch

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from notification.models import Client
from notification.utils.test_utils import MockFirebaseSendEach, apply_firebase_patches


class TestNotificationInitView(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.applied_patches = apply_firebase_patches(cls)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        for p in cls.applied_patches:
            p.stop()

    def setUp(self) -> None:
        super().setUp()

        self.api_url = reverse("notification-create-notification")

    @patch(
        "notification.services.push.messaging.send_each",
    )
    def test_init_notification_success(self, multicast_mock):
        multicast_mock.return_value = MockFirebaseSendEach(5)

        client = Client(
            external_id="abc", firebase_token="abc_token", receive_push=True
        )
        client.save()

        data = {
            "title": "foobar title",
            "body": "foobar body",
            "module_slug": "foobar module slug",
            "context": {"foo": "bar"},
            "created_at": "2024-10-31T15:00:00",
            "client_ids": [client.external_id, "def", "ghi"],
        }

        result = self.client.post(
            self.api_url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 200)

    @override_settings(MAX_CLIENTS_PER_REQUEST=5)
    def test_too_many_clients(self):
        data = {
            "title": "foobar",
            "body": "something",
            "context_json": {"foo": "bar"},
            "created_at": "2024-10-31T15:00:00",
            "client_ids": [
                f"client_{i}" for i in range(settings.MAX_CLIENTS_PER_REQUEST + 1)
            ],
        }

        result = self.client.post(
            self.api_url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(result.status_code, 400)
        self.assertContains(result, "Too many client ids", status_code=400)
