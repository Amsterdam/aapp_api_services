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
    def test_success_get_service_maps_view_no_module_source(self):

        url = reverse("service-maps")
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        # by default, the module_source should be "handig-in-de-stad", so we should only get the services with that input_module
        expected_services = [
            service
            for service in Services.choices_as_list()
            if service["input_module"] == "handig-in-de-stad"
        ]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(expected_services))
        self.assertEqual(
            sorted(s["title"] for s in response.data),
            sorted(s["title"] for s in expected_services),
        )

    def test_success_get_service_maps_view_handig_in_de_stad(self):
        url = reverse("service-maps")
        data = {"module_source": "handig-in-de-stad"}
        response = self.client.get(
            url,
            data,
            headers=self.api_headers,
        )

        expected_services = [
            service
            for service in Services.choices_as_list()
            if service["input_module"] == "handig-in-de-stad"
        ]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(expected_services))
        self.assertEqual(
            sorted(s["title"] for s in response.data),
            sorted(s["title"] for s in expected_services),
        )

    def test_success_get_service_maps_view_koningsdag(self):
        url = reverse("service-maps")
        data = {"module_source": "koningsdag"}
        response = self.client.get(url, data, headers=self.api_headers)
        expected_services = [
            service
            for service in Services.choices_as_list()
            if service["input_module"] == "koningsdag"
        ]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(expected_services))
        self.assertEqual(
            sorted(s["title"] for s in response.data),
            sorted(s["title"] for s in expected_services),
        )

    def test_success_get_service_maps_view_invalid(self):
        url = reverse("service-maps")
        data = {"module_source": "invalid_module"}
        response = self.client.get(url, data, headers=self.api_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


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
