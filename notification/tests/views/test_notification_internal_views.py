import json
from unittest.mock import patch

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from notification.models import Client
from notification.utils.patch_utils import (
    MockFirebaseSendEach,
    apply_init_firebase_patches,
)


@pytest.fixture(scope="module", autouse=True)
def apply_patches():
    applied_patches = apply_init_firebase_patches()
    yield
    for p in applied_patches:
        p.stop()


@pytest.fixture
def api_url():
    return reverse("notification-create-notification")


@pytest.mark.django_db
@patch("notification.services.push.messaging.send_each")
def test_init_notification_success(
    multicast_mock, api_client, api_url, firebase_messages
):
    client = Client(external_id="abc", firebase_token="abc_token")
    client.save()

    data = {
        "title": "foobar title",
        "body": "foobar body",
        "module_slug": "foobar module slug",
        "context": {"foo": "bar"},
        "created_at": "2024-10-31T15:00:00",
        "client_ids": [client.external_id, "def", "ghi"],
    }

    messages = firebase_messages([client], title=data["title"], body=data["body"])
    multicast_mock.return_value = MockFirebaseSendEach(messages)

    result = api_client.post(
        api_url,
        data=json.dumps(data),
        content_type="application/json",
    )
    assert result.status_code == 200


@override_settings(MAX_CLIENTS_PER_REQUEST=5)
def test_too_many_clients(api_client, api_url):
    data = {
        "title": "foobar",
        "body": "something",
        "context_json": {"foo": "bar"},
        "created_at": "2024-10-31T15:00:00",
        "client_ids": [
            f"client_{i}" for i in range(settings.MAX_CLIENTS_PER_REQUEST + 1)
        ],
    }

    result = api_client.post(
        api_url,
        data=json.dumps(data),
        content_type="application/json",
    )
    assert result.status_code == 400
    assert "Too many client ids" in result.content.decode()
