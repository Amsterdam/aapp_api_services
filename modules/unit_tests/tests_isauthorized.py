from unittest.mock import patch

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from django.test import Client, TestCase

from modules.models import AppRelease, Module
from modules.unit_tests.unit_test_mock_data import TestData

mock_private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)
mock_pem = mock_private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)
mock_public_key = mock_private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)


class TestIsAuthorized(TestCase):
    def setUp(self):
        patcher = patch('modules.generic_functions.is_authorized.IsAuthorized.get_signing_key')
        self.mock_get_signing_key = patcher.start()
        self.mock_get_signing_key.return_value = mock_public_key
        self.addCleanup(patcher.stop)

        self.client = Client()
        payload = {
            "iss": f"https://sts.windows.net/{settings.TENANT_ID}/",
            "aud": f"api://{settings.CLIENT_ID}",
            "scp": "Modules.Edit"
        }
        self.jwt_token = "Bearer " + jwt.encode(payload, mock_private_key, algorithm="RS256")

        self.data = TestData()
        modules: list[Module] = []
        releases: list[AppRelease] = []

        for module in self.data.modules:
            module = Module.objects.create(**module)
            modules.append(module)

        for release in self.data.releases:
            release = AppRelease.objects.create(**release)
            releases.append(release)

    def test_invalid_token(self):
        response = self.client.post(
            "/modules/api/v1/module",
            data={},
            HTTP_AUTHORIZATION="Bearer invalid",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.reason_phrase, "Forbidden")
        self.assertEqual(response.content, b'{"error": "Error validating token"}')

    def test_no_token(self):
        response = self.client.post(
            "/modules/api/v1/module",
            data={},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.reason_phrase, "Unauthorized")
        self.assertEqual(response.content, b'{"error": "Authorization header is missing"}')

    def test_jwt_token_valid(self):
        data = {'slug': 'something'}
        response = self.client.post(
            "/modules/api/v1/module",
            data=data,
            HTTP_AUTHORIZATION=self.jwt_token,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

    def test_jwt_token_invalid(self):
        response = self.client.post(
            "/modules/api/v1/module",
            data={},
            HTTP_AUTHORIZATION="bogus",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.reason_phrase, "Unauthorized")

    def test_release_version_endpoint(self):
        """ 
        The release version endpoint should be publically accessible
        """
        response = self.client.get(
            "/modules/api/v1/release/0.0.1",
            accept="application/json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            "/modules/api/v1/release/0.0.1",
            HTTP_AUTHORIZATION=self.jwt_token,
            accept="application/json",
        )
        self.assertEqual(response.status_code, 200)
        