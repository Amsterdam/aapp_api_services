from unittest.mock import patch

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from django.test import TestCase

mock_private_key = rsa.generate_private_key(
    public_exponent=65537, key_size=2048, backend=default_backend()
)
mock_public_key = mock_private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)


def apply_signing_key_patch(test_case: TestCase) -> None:
    patcher = patch("core.authentication.EntraTokenMixin._get_signing_key")
    test_case.mock_get_signing_key = patcher.start()
    test_case.mock_get_signing_key.return_value = mock_public_key
    return patcher


def create_jwt_token(
    groups: list[str] = None,
    email: str = None,
    first_name: str = None,
    last_name: str = None,
) -> str:
    payload = {
        "aud": f"api://{settings.ENTRA_CLIENT_ID}",
        "iss": f"https://sts.windows.net/{settings.ENTRA_TENANT_ID}/",
        "groups": groups,
        "upn": email,
        "family_name": last_name,
        "given_name": first_name,
        "name": f"{last_name}, {first_name}",
    }
    return jwt.encode(payload, mock_private_key, algorithm="RS256")
