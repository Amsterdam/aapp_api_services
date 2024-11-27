import logging
from unittest.mock import patch

import pytest
from django.conf import settings
from django.test import override_settings

from notification.models import Device, Notification
from notification.services.push import PushService, PushServiceDeviceLimitError
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
def unsaved_notification():
    return Notification(
        title="foobar title",
        body="foobar body",
        module_slug="foobar-slug",
        context={"some": "context"},
        created_at="2024-10-31T16:30",
    )


@pytest.fixture
def device():
    device = Device(external_id="abc", firebase_token="abc_token")
    device.save()
    return device


@pytest.fixture
def devices():
    def _create_devices(amount: int, with_token=True, start_id=0):
        new_devices = []
        mock_token = "abc_token" if with_token else None
        for i in range(start_id, start_id + amount):
            device = Device(external_id=f"abc_{i}", firebase_token=mock_token)
            device.save()
            new_devices.append(device)
        return new_devices

    return _create_devices


@pytest.mark.django_db
@patch("notification.services.push.messaging.send_each")
def test_push_success(multicast_mock, unsaved_notification, device, firebase_messages):
    messages = firebase_messages(
        [device], title=unsaved_notification.title, body=unsaved_notification.body
    )
    multicast_mock.return_value = MockFirebaseSendEach(messages)

    push_service = PushService(unsaved_notification, [device.external_id])
    push_service.push()

    notification = Notification.objects.filter(
        device__external_id=device.external_id
    ).first()
    assert notification.pushed_at is not None


@pytest.mark.django_db
@patch("notification.services.push.messaging.send_each")
def test_push_with_some_failed_tokens(
    multicast_mock, unsaved_notification, devices, firebase_messages, caplog
):
    device_count = 5
    failed_device_count = 2

    created_devices = devices(device_count)
    messages = firebase_messages(
        created_devices,
        title=unsaved_notification.title,
        body=unsaved_notification.body,
    )

    multicast_mock.return_value = MockFirebaseSendEach(
        messages, fail_count=failed_device_count
    )

    push_service = PushService(
        unsaved_notification, [c.external_id for c in created_devices]
    )

    # Set up logger
    logger = logging.getLogger("notification.services.push")
    parent_logger = logger.parent
    parent_logger.setLevel(logging.INFO)
    parent_logger.propagate = True

    with caplog.at_level(logging.INFO, logger="notification.services.push"):
        result = push_service.push()

    # Check if the specific log messages are in the captured logs
    assert any(
        "Failed to send notification to device" in record.message
        for record in caplog.records
    )
    assert Notification.objects.count() == device_count
    assert result["failed_token_count"] == failed_device_count


@override_settings(FIREBASE_DEVICE_LIMIT=5)
def test_hit_max_devices():
    device_ids = [f"device_{i}" for i in range(settings.FIREBASE_DEVICE_LIMIT + 1)]

    with pytest.raises(PushServiceDeviceLimitError):
        PushService(None, device_ids)


@pytest.mark.django_db
def test_device_without_firebase_tokens(unsaved_notification, devices, caplog):
    created_devices = devices(5, with_token=False)
    device_ids = [c.external_id for c in created_devices]

    push_service = PushService(unsaved_notification, device_ids)

    # Ensure the logger is set to the correct level
    logger = logging.getLogger("notification.services.push")

    parent_logger = logger.parent
    parent_logger.setLevel(logging.INFO)
    parent_logger.propagate = True

    with caplog.at_level(logging.INFO, logger="notification.services.push"):
        result = push_service.push()

    # For each device a notification should have been created
    for c in created_devices:
        notification = Notification.objects.filter(
            device__external_id=c.external_id
        ).first()
        assert notification is not None

    # Check if the specific log message is in the captured logs
    assert any(
        "none of the devices have a Firebase token" in record.message
        for record in caplog.records
    )
    assert Notification.objects.count() == len(created_devices)
    assert result == {
        "devices_with_token_count": 0,
        "failed_token_count": 0,
        "total_device_count": 5,
        "unknown_device_count": 0,
    }


@pytest.mark.django_db
def test_notifications_created_for_unregistered_device(unsaved_notification):
    device_ids = ["unregistered_device_id"]
    push_service = PushService(unsaved_notification, device_ids)
    push_service.push()

    notification = Notification.objects.filter(
        device__external_id=device_ids[0]
    ).first()
    assert notification is not None


@pytest.mark.django_db
@patch("notification.services.push.messaging.send_each")
def test_notifications_created_for_unknown_devices(
    multicast_mock, firebase_messages, devices, unsaved_notification
):
    devices_with_token = devices(3, with_token=True)

    messages = firebase_messages(
        devices_with_token,
        title=unsaved_notification.title,
        body=unsaved_notification.body,
    )
    multicast_mock.return_value = MockFirebaseSendEach(messages)

    unknown_device_ids = ["unknown_1", "unknown_2", "unknown_3"]
    all_device_ids = [
        known_device.external_id for known_device in devices_with_token
    ] + unknown_device_ids

    push_service = PushService(unsaved_notification, all_device_ids)
    push_service.push()

    notifications = Notification.objects.filter(
        device__external_id__in=unknown_device_ids
    ).all()
    assert len(notifications) == len(unknown_device_ids)


@pytest.mark.django_db
@patch("notification.services.push.messaging.send_each")
def test_response_data_counts_for_devices(
    multicast_mock, firebase_messages, devices, unsaved_notification
):
    devices_with_token = devices(3, with_token=True)
    devices_without_token = devices(
        3, with_token=False, start_id=len(devices_with_token)
    )
    known_devices = devices_with_token + devices_without_token

    messages = firebase_messages(
        known_devices, title=unsaved_notification.title, body=unsaved_notification.body
    )
    multicast_mock.return_value = MockFirebaseSendEach(messages, fail_count=1)

    unknown_device_ids = ["unknown_1", "unknown_2", "unknown_3"]
    all_device_ids = [
        known_device.external_id for known_device in known_devices
    ] + unknown_device_ids

    push_service = PushService(unsaved_notification, all_device_ids)
    response_data = push_service.push()

    assert response_data == {
        "devices_with_token_count": len(devices_with_token),
        "failed_token_count": 1,
        "total_device_count": len(all_device_ids),
        "unknown_device_count": len(unknown_device_ids),
    }
