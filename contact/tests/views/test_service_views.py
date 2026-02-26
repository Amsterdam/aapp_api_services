import responses
from django.conf import settings
from django.urls import reverse
from rest_framework import status

from contact.tests.mock_data import toilets
from core.tests.test_authentication import BasicAPITestCase


class TestServiceMapView(BasicAPITestCase):
    def test_success_get_service_map_view(self):
        # Mock the response from the external API
        responses.get(settings.PUBLIC_TOILET_URL, json=toilets.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 1})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("filters", response.data)
        self.assertIn("properties_to_include", response.data)
        self.assertIn("data", response.data)

    def test_not_implemented_get_service_map_view(self):
        # Mock the response from the external API

        url = reverse(
            "service-map", kwargs={"service_id": 999}
        )  # Non-existing service_id
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Service not found.")
