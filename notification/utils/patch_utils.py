import atexit
import logging
from unittest.mock import patch

from django.conf import settings

logger = logging.getLogger(__name__)


def apply_init_firebase_patches():
    """Apply patches to Firebase initialization functions for testing."""
    settings.FIREBASE_CREDENTIALS = "{}"

    cert_patcher = patch("notification.services.push.credentials.Certificate")
    init_patcher = patch("notification.services.push.firebase_admin.initialize_app")
    app_patcher = patch("notification.services.push.firebase_admin.get_app")

    # Start patches and set return values to None
    mock_cert = cert_patcher.start()
    mock_cert.return_value = None

    mock_init = init_patcher.start()
    mock_init.return_value = None

    mock_app = app_patcher.start()
    mock_app.return_value = None

    return cert_patcher, init_patcher, app_patcher


class MockFirebaseError(Exception):
    """Custom exception for mock Firebase errors."""

    pass


class MockFirebaseSendEachResponse:
    """Mock response for the `send_each` function from the `firebase_admin.messaging` module."""

    def __init__(self, success=True):
        self.success = success


class MockFirebaseSendEach:
    """Mock for the `send_each` function from the `firebase_admin.messaging` module."""

    def __init__(self, messages: list, fail_count: int = 0):
        if fail_count > len(messages):
            raise MockFirebaseError("Fail count cannot be higher than response count")

        self.failure_count = fail_count
        self.responses: list[MockFirebaseSendEachResponse] = [
            MockFirebaseSendEachResponse() for _ in messages
        ]

        # Mark the first `fail_count` responses as failures
        for response in self.responses[:fail_count]:
            response.success = False

        # Log each message
        for message in messages:
            log_message = (
                "Mocked outgoing Firebase message!\n"
                f"- title: {message.notification.title}\n"
                f"- token: {message.token}\n"
                f"- data: {message.data}"
            )

            if message.android:
                log_message += f"\n- android_image: {message.android.notification.image}"
            
            if message.apns:
                log_message += f"\n- ios_image: {message.apns.fcm_options.image}"

            logger.debug(log_message)


def setup_local_development_patches():
    """Set up patches for local development to mock Firebase interactions."""
    cert_patcher, init_patcher, app_patcher = apply_init_firebase_patches()
    send_each_patcher = patch(
        "notification.services.push.messaging.send_each", new=MockFirebaseSendEach
    )
    send_each_patcher.start()

    # Ensure patches are stopped when the server stops
    atexit.register(cert_patcher.stop)
    atexit.register(init_patcher.stop)
    atexit.register(app_patcher.stop)
    atexit.register(send_each_patcher.stop)
