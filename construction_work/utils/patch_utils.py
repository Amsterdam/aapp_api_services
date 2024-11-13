import uuid
from unittest.mock import MagicMock, patch

import jwt
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

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
    groups: list[str] = None,
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


class MockNotificationResponse:
    def __init__(self, title, body, warning_id=1, status_code=200):
        self.warning_id = warning_id
        self.title = title
        self.body = body
        self.status_code = status_code

    def get_response(self):
        mock_response = MagicMock()
        mock_response.json = self.json
        mock_response.status_code = self.status_code
        mock_response.raise_for_status = self.raise_for_status
        return mock_response

    def json(self):
        return {
            "push_message": {
                "title": self.title,
                "body": self.body,
                "module_slug": "construction-work",
                "context": {
                    "linkSourceid": self.warning_id,
                    "type": "ProjectWarningCreatedByProjectManager",
                    "notificationId": str(uuid.uuid4()),
                },
                "created_at": timezone.now().isoformat(),
                "is_read": False,
            }
        }

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise requests.exceptions.HTTPError(f"{self.status_code} Error")
