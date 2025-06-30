import re

import responses
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse

from bridge.proxy.tests import mock_data
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class BaseProxyViewTestCase(ResponsesActivatedAPITestCase):
    def assert_caching(self, request_body=None):
        # First call
        response = self.client.get(self.url, request_body, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(cache.keys("*")), 2
        )  # The request and the headers are cached both as separate keys
        self.assertEqual(self.rsp_get.call_count, 1)

        # Second call
        response = self.client.get(self.url, request_body, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(cache.keys("*")), 2)
        self.assertEqual(
            self.rsp_get.call_count, 1
        )  # The request should not be called a second time!


class TestWasteGuideView(BaseProxyViewTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("waste-guide-search")
        self.rsp_get = responses.get(
            re.compile(settings.WASTE_GUIDE_URL + ".*"), json=mock_data.ADDRESS_DATA
        )

    def test_waste_guide_view(self):
        self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(self.rsp_get.call_count, 1)

    def test_cache(self):
        self.assert_caching()


class TestAddressSearchByNameView(BaseProxyViewTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("address-search-by-name")
        self.rsp_get = responses.get(
            re.compile(settings.ADDRESS_SEARCH_URL + ".*"), json=mock_data.ADDRESS_DATA
        )

    def test_success(self):
        response = self.client.get(
            self.url, {"query": "amstel"}, headers=self.api_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.rsp_get.call_count, 1)
        self.assertEqual(len(response.data), 3)

    def test_with_street_success(self):
        response = self.client.get(
            self.url,
            {"query": "amstel 1", "street_name": "amstel"},
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.rsp_get.call_count, 1)
        self.assertEqual(len(response.data), 3)

    def test_with_coordinates_exception(self):
        response = self.client.get(
            self.url,
            {"lat": "52.7", "lon": "3.15"},
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.rsp_get.call_count, 0)

    def test_cache(self):
        self.assert_caching({"query": "amstel"})


class TestAddressSearchByCoordinateView(BaseProxyViewTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("address-search-by-coordinate")
        self.rsp_get = responses.get(
            re.compile(settings.ADDRESS_SEARCH_URL + ".*"), json=mock_data.ADDRESS_DATA
        )

    def test_success(self):
        response = self.client.get(
            self.url,
            {"lat": "52.7", "lon": "3.15"},
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.rsp_get.call_count, 1)
        self.assertEqual(len(response.data), 3)

    def test_with_query_exception(self):
        response = self.client.get(
            self.url, {"query": "amstel 1"}, headers=self.api_headers
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.rsp_get.call_count, 0)

    def test_cache(self):
        self.assert_caching({"lat": "50.7", "lon": "3.15"})
