import base64
from unittest.mock import patch

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from django.test import Client

from modules.tests.mock_data import TestCaseWithData


class TestCaseWithAuth(TestCaseWithData):
    def setUp(self):
        # Generate RSA key pair for testing
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )

        patcher = patch("azure_ad_verify_token.verify.get_jwk")
        mock_get_jwk = patcher.start()
        mock_get_jwk.return_value = self._get_jwk()
        self.addCleanup(patcher.stop)

        # Add mock token and client
        self.jwt_token = f"Bearer {self.get_jwt_token()}"
        self.client = Client()

        # Collect testdata
        super().setUp()

    def get_jwt_token(self, token_payload=None):
        if token_payload is None:
            token_payload = {
                "aud": f"api://{settings.CLIENT_ID}",
                "iss": f"https://sts.windows.net/{settings.TENANT_ID}/",
                "unique_name": "test_user",
                "scp": "Modules.Edit",
            }
        token = jwt.encode(
            payload=token_payload,
            key=self.private_key,
            algorithm="RS256",
            headers={"kid": "test-key-id"},
        )
        return token

    def _get_jwk(self):
        self.public_key = self.private_key.public_key()
        public_numbers = self.public_key.public_numbers()
        e = public_numbers.e
        n = public_numbers.n

        def long_to_base64(value):
            return (
                base64.urlsafe_b64encode(
                    value.to_bytes((value.bit_length() + 7) // 8, "big")
                )
                .rstrip(b"=")
                .decode("ascii")
            )

        return {
            "kty": "RSA",
            "use": "sig",
            "kid": "test-key-id",
            "n": long_to_base64(n),
            "e": long_to_base64(e),
        }
