from django.conf import settings
from rest_framework import status

from modules.tests.setup import TestCaseWithAuth


class ModuleEndpointTestCase(TestCaseWithAuth):
    def setUp(self):
        self.url = "/modules/api/v1/module/"
        super().setUp()

    def test_valid_token(self):
        token = self.get_jwt_token()

        # Make a request to the endpoint
        data = {"slug": "something"}
        response = self.client.post(
            self.url,
            HTTP_AUTHORIZATION=f"Bearer {token}",
            data=data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_scope(self):
        # Token with invalid scope
        token_payload = {
            "aud": f"api://{settings.CLIENT_ID}",
            "iss": f"https://sts.windows.net/{settings.TENANT_ID}/",
            "unique_name": "test_user",
            "scp": "Modules.Read",
        }
        token = self.get_jwt_token(token_payload)

        # Make a request to the endpoint
        data = {"slug": "something"}
        response = self.client.post(
            self.url,
            HTTP_AUTHORIZATION=f"Bearer {token}",
            data=data,
            content_type="application/json",
        )
        self.assertContains(
            response,
            "Token does not have required scope",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    def test_invalid_token(self):
        data = {"slug": "something"}
        response = self.client.post(
            self.url,
            HTTP_AUTHORIZATION="Bearer invalid_token",
            data=data,
            content_type="application/json",
        )
        self.assertContains(
            response, "token_not_valid", status_code=status.HTTP_401_UNAUTHORIZED
        )

    def test_no_token(self):
        data = {"slug": "something"}
        response = self.client.post(
            self.url,
            HTTP_AUTHORIZATION=None,
            data=data,
            content_type="application/json",
        )
        self.assertContains(
            response,
            "Authentication credentials were not provided",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    def test_release_version_endpoint(self):
        """
        The release version endpoint should be publicly accessible
        """
        data = {"slug": "something"}
        response = self.client.get(
            "/modules/api/v1/release/0.0.1/",
            HTTP_AUTHORIZATION=None,
            data=data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
