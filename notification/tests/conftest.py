import pytest
from firebase_admin import messaging
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def firebase_messages():
    def _create_messages(created_clients, title="test title", body="test body"):
        messages = []
        for client in created_clients:
            firebase_message = messaging.Message(
                data={},
                notification=messaging.Notification(title=title, body=body),
                token=client.firebase_token,
            )
            messages.append(firebase_message)
        return messages

    return _create_messages
