import responses
from django.conf import settings
from django.urls import reverse
from rest_framework import status

from contact.enums.services import Services
from contact.enums.toilets import ToiletFilters, ToiletProperties
from contact.tests.mock_data import toilets
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class TestServiceMapsView(ResponsesActivatedAPITestCase):
    def test_success_get_service_maps_view(self):

        url = reverse("service-maps")
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(Services.choices()))


class TestServiceMapView(ResponsesActivatedAPITestCase):
    def test_success_get_service_map_view(self):
        # Mock the response from the external API
        responses.get(settings.PUBLIC_TOILET_URL, json=toilets.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 1})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["filters"], ToiletFilters.choices())
        self.assertEqual(
            response.data["properties_to_include"], ToiletProperties.choices()
        )
        self.assertEqual(len(response.data["data"]), len(toilets.MOCK_DATA["features"]))

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
