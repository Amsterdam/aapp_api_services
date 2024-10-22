from unittest.mock import patch

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase


def create_image_file(image_path):
    with open(image_path, "rb") as image_file:
        image_file = SimpleUploadedFile(
            name="image.jpg",
            content=image_file.read(),
            content_type="image/jpeg",
        )
    return image_file


mock_private_key = rsa.generate_private_key(
    public_exponent=65537, key_size=2048, backend=default_backend()
)
mock_public_key = mock_private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)


def apply_signing_key_patch(test_case: TestCase) -> None:
    patcher = patch(
        "construction_work.authentication.EntraIDAuthentication._get_signing_key"
    )
    test_case.mock_get_signing_key = patcher.start()
    test_case.mock_get_signing_key.return_value = mock_public_key
    return patcher


def create_jwt_token(
    groups: list[str] = [],
    scope="Modules.Edit",
    email: str = None,
    first_name: str = None,
    last_name: str = None,
) -> str:
    payload = {
        "aud": f"api://{settings.ENTRA_CLIENT_ID}",
        "iss": f"https://sts.windows.net/{settings.ENTRA_TENANT_ID}/",
        "groups": groups,
        "scp": scope,
        "upn": email,
        "family_name": last_name,
        "given_name": first_name,
    }
    return "Bearer " + jwt.encode(payload, mock_private_key, algorithm="RS256")


def create_image_file(image_path):
    with open(image_path, "rb") as image_file:
        image_file = SimpleUploadedFile(
            name="image.jpg",
            content=image_file.read(),
            content_type="image/jpeg",
        )
    return image_file


def apply_firebase_patches(test_case: TestCase) -> list:
    settings.FIREBASE_CREDENTIALS = "{}"

    cert_patcher = patch(
        "construction_work.services.push_notifications.credentials.Certificate"
    )
    test_case.mock_cert = cert_patcher.start()
    test_case.mock_cert.return_value = None

    init_patcher = patch(
        "construction_work.services.push_notifications.firebase_admin.initialize_app"
    )
    test_case.mock_init = init_patcher.start()
    test_case.mock_init.return_value = None

    app_patcher = patch(
        "construction_work.services.push_notifications.firebase_admin.get_app"
    )
    test_case.mock_app = app_patcher.start()
    test_case.mock_app.return_value = None

    return cert_patcher, init_patcher, app_patcher


class MockFirebaseError(Exception):
    pass


class MockFirebaseMulticastResponse:
    def __init__(self, success=True):
        self.success = success


class MockFirebaseSendMulticast:
    def __init__(self, response_count: int, fail_count: int = 0):
        if fail_count > response_count:
            raise MockFirebaseError("Fail count can not be higher then response count")

        self.failure_count = fail_count
        self.responses: list[MockFirebaseMulticastResponse] = []
        for _ in range(0, response_count):
            self.responses.append(MockFirebaseMulticastResponse())

        failed_responses = self.responses[0:fail_count]
        for x in failed_responses:
            x.success = False
