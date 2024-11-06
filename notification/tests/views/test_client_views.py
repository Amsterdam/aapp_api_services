from django.conf import settings
from django.urls import reverse

from core.tests import BasicAPITestCase
from notification.models import Client


class TestClientRegisterView(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.api_url = reverse("notification-register-client")

    def test_registration_ok(self):
        """Test registering a new client"""
        data = {"firebase_token": "foobar_token", "os": "ios"}
        self.api_headers[settings.HEADER_CLIENT_ID] = "0"
        first_result = self.client.post(self.api_url, data, headers=self.api_headers)

        self.assertEqual(first_result.status_code, 200)
        self.assertEqual(
            first_result.data.get("firebase_token"), data.get("firebase_token")
        )
        self.assertEqual(first_result.data.get("os"), data.get("os"))

        # Silent discard second call
        second_result = self.client.post(self.api_url, data, headers=self.api_headers)

        self.assertEqual(second_result.status_code, 200)
        self.assertEqual(
            second_result.data.get("firebase_token"), data.get("firebase_token")
        )
        self.assertEqual(second_result.data.get("os"), data.get("os"))

        # Assert only one record in db
        clients_with_token = list(
            Client.objects.filter(firebase_token__isnull=False).all()
        )
        self.assertEqual(len(clients_with_token), 1)

    def test_delete_registration(self):
        """Test removing a client registration"""
        new_client = Client(
            external_id="foobar_client", firebase_token="foobar_token", os="os"
        )
        new_client.save()

        # Delete registration
        self.api_headers[settings.HEADER_CLIENT_ID] = "foobar_client"
        first_result = self.client.delete(self.api_url, headers=self.api_headers)

        self.assertEqual(first_result.status_code, 200)
        self.assertEqual(first_result.data, "Registration removed")

        # Expect no records in db
        clients_with_token = list(
            Client.objects.filter(firebase_token__isnull=False).all()
        )
        self.assertEqual(len(clients_with_token), 0)

        # Silently discard not existing registration delete
        second_result = self.client.delete(self.api_url, headers=self.api_headers)

        self.assertEqual(second_result.status_code, 200)
        self.assertEqual(second_result.data, "Registration removed")

    def test_delete_no_client(self):
        self.api_headers[settings.HEADER_CLIENT_ID] = "non-existing-client-id"
        first_result = self.client.delete(self.api_url, headers=self.api_headers)

        self.assertEqual(first_result.status_code, 200)

    def test_missing_os_missing(self):
        """Test if missing OS is detected"""
        data = {"firebase_token": "0"}
        self.api_headers[settings.HEADER_CLIENT_ID] = "foobar"
        result = self.client.post(self.api_url, data, headers=self.api_headers)

        self.assertEqual(result.status_code, 400)

    def test_missing_firebase_token(self):
        """Test is missing token is detected"""
        data = {"os": "ios"}
        self.api_headers[settings.HEADER_CLIENT_ID] = "foobar"
        result = self.client.post(self.api_url, data, headers=self.api_headers)

        self.assertEqual(result.status_code, 400)

    def test_missing_client_id(self):
        """Test if missing identifier is detected"""
        data = {"firebase_token": "0", "os": "ios"}
        result = self.client.post(self.api_url, data, headers=self.api_headers)

        self.assertEqual(result.status_code, 400)
