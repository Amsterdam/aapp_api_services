import logging
from unittest.mock import patch

import pytest
from django.conf import settings
from django.test import override_settings

from notification.models import Client, Notification
from notification.services.push import PushService, PushServiceClientLimitError
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
def client():
    client = Client(external_id="abc", firebase_token="abc_token")
    client.save()
    return client


@pytest.fixture
def clients():
    def _create_clients(amount: int, with_token=True):
        new_clients = []
        mock_token = "abc_token" if with_token else None
        for i in range(amount):
            client = Client(external_id=f"abc_{i}", firebase_token=mock_token)
            client.save()
            new_clients.append(client)
        return new_clients

    return _create_clients


@pytest.mark.django_db
@patch("notification.services.push.messaging.send_each")
def test_push_success(multicast_mock, unsaved_notification, client, firebase_messages):
    messages = firebase_messages(
        [client], title=unsaved_notification.title, body=unsaved_notification.body
    )
    multicast_mock.return_value = MockFirebaseSendEach(messages)

    push_service = PushService(unsaved_notification, [client.external_id])
    push_service.push()

    notification = Notification.objects.filter(
        client__external_id=client.external_id
    ).first()
    assert notification.pushed_at is not None


@pytest.mark.django_db
@patch("notification.services.push.messaging.send_each")
def test_push_with_some_failed_tokens(
    multicast_mock, unsaved_notification, clients, firebase_messages, caplog
):
    client_count = 5
    failed_client_count = 2

    created_clients = clients(client_count)
    messages = firebase_messages(
        created_clients,
        title=unsaved_notification.title,
        body=unsaved_notification.body,
    )

    multicast_mock.return_value = MockFirebaseSendEach(
        messages, fail_count=failed_client_count
    )

    push_service = PushService(
        unsaved_notification, [c.external_id for c in created_clients]
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
        "Failed to send notification to client" in record.message
        for record in caplog.records
    )
    assert Notification.objects.count() == client_count
    assert result["failed_token_count"] == failed_client_count


@override_settings(FIREBASE_CLIENT_LIMIT=5)
def test_hit_max_clients():
    client_ids = [f"client_{i}" for i in range(settings.FIREBASE_CLIENT_LIMIT + 1)]

    with pytest.raises(PushServiceClientLimitError):
        PushService(None, client_ids)


@pytest.mark.django_db
def test_client_without_firebase_tokens(unsaved_notification, clients, caplog):
    created_clients = clients(5, with_token=False)
    client_ids = [c.external_id for c in created_clients]

    push_service = PushService(unsaved_notification, client_ids)

    # Ensure the logger is set to the correct level
    logger = logging.getLogger("notification.services.push")

    parent_logger = logger.parent
    parent_logger.setLevel(logging.INFO)
    parent_logger.propagate = True

    with caplog.at_level(logging.INFO, logger="notification.services.push"):
        result = push_service.push()

    # For each client a notification should have been created
    for c in created_clients:
        notification = Notification.objects.filter(
            client__external_id=c.external_id
        ).first()
        assert notification is not None

    # Check if the specific log message is in the captured logs
    assert any(
        "none of the clients have a Firebase token" in record.message
        for record in caplog.records
    )
    assert Notification.objects.count() == len(created_clients)
    assert result["total_token_count"] == 0
    assert result["failed_token_count"] == 0
