import responses
from django.conf import settings
from django.urls import reverse
from rest_framework import status

from contact.enums.services import Services
from contact.enums.taps import TapFilters, TapProperties
from contact.enums.toilets import ToiletFilters, ToiletProperties
from contact.tests.mock_data import taps, toilets
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class TestServiceMapsView(ResponsesActivatedAPITestCase):
    def test_success_get_service_maps_view(self):

        url = reverse("service-maps")
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(Services.choices_as_list()))


class TestServiceMapView(ResponsesActivatedAPITestCase):
    def test_success_get_service_map_view_toilets(self):
        # Mock the response from the external API
        responses.get(settings.PUBLIC_TOILET_URL, json=toilets.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 1})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["filters"], ToiletFilters.choices_as_list())
        self.assertEqual(
            response.data["properties_to_include"], ToiletProperties.choices_as_list()
        )
        self.assertEqual(
            len(response.data["data"]["features"]), len(toilets.MOCK_DATA["features"])
        )

    def test_success_get_service_map_view_taps(self):
        # Mock the response from the external API
        responses.get(settings.TAP_URL, json=taps.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 2})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["filters"], TapFilters.choices_as_list())
        self.assertEqual(
            response.data["properties_to_include"], TapProperties.choices_as_list()
        )

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
