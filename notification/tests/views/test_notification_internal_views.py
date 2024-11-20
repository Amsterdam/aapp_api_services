import json
from unittest.mock import patch

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from notification.models import Device
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
    device = Device(external_id="abc", firebase_token="abc_token")
    device.save()

    data = {
        "title": "foobar title",
        "body": "foobar body",
        "module_slug": "foobar module slug",
        "context": {"foo": "bar"},
        "created_at": "2024-10-31T15:00:00",
        "device_ids": [device.external_id, "def", "ghi"],
    }

    messages = firebase_messages([device], title=data["title"], body=data["body"])
    multicast_mock.return_value = MockFirebaseSendEach(messages)

    result = api_client.post(
        api_url,
        data=json.dumps(data),
        content_type="application/json",
    )
    assert result.status_code == 201
    response = result.json()
    response["missing_device_ids"].sort()
    assert response == {
        "total_device_count": 3,
        "total_create_count": 1,
        "total_token_count": 1,
        "failed_token_count": 0,
        "missing_device_ids": ["def", "ghi"],
    }


@override_settings(MAX_DEVICES_PER_REQUEST=5)
def test_too_many_devices(api_client, api_url):
    data = {
        "title": "foobar",
        "body": "something",
        "context_json": {"foo": "bar"},
        "created_at": "2024-10-31T15:00:00",
        "device_ids": [
            f"device_{i}" for i in range(settings.MAX_DEVICES_PER_REQUEST + 1)
        ],
    }

    result = api_client.post(
        api_url,
        data=json.dumps(data),
        content_type="application/json",
    )
    assert result.status_code == 400
    assert "Too many device ids" in result.content.decode()
