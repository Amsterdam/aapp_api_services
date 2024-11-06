from unittest.mock import patch

from django.conf import settings
from django.test import TestCase


def apply_firebase_patches(test_case: TestCase) -> list:
    settings.FIREBASE_CREDENTIALS = "{}"

    cert_patcher = patch("notification.services.push.credentials.Certificate")
    test_case.mock_cert = cert_patcher.start()
    test_case.mock_cert.return_value = None

    init_patcher = patch("notification.services.push.firebase_admin.initialize_app")
    test_case.mock_init = init_patcher.start()
    test_case.mock_init.return_value = None

    app_patcher = patch("notification.services.push.firebase_admin.get_app")
    test_case.mock_app = app_patcher.start()
    test_case.mock_app.return_value = None

    return cert_patcher, init_patcher, app_patcher


class MockFirebaseError(Exception):
    pass


class MockFirebaseSendEachResponse:
    def __init__(self, success=True):
        self.success = success


class MockFirebaseSendEach:
    def __init__(self, response_count: int, fail_count: int = 0):
        if fail_count > response_count:
            raise MockFirebaseError("Fail count can not be higher then response count")

        self.failure_count = fail_count
        self.responses: list[MockFirebaseSendEachResponse] = []
        for _ in range(0, response_count):
            self.responses.append(MockFirebaseSendEachResponse())

        failed_responses = self.responses[0:fail_count]
        for x in failed_responses:
            x.success = False
