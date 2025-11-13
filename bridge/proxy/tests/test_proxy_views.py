import re

import responses
from django.conf import settings
from django.urls import reverse

from bridge.proxy.tests import mock_data
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class TestEgisProxyView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("egis-proxy", args=["some/path"])

    def test_proxy_view_get(self):
        rsp_get = responses.get(
            re.compile(settings.SSP_BASE_URL_V2 + "/some/path.*"),
            json={"key": "value"},
        )
        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"key": "value"})
        self.assertEqual(rsp_get.call_count, 1)

    def test_proxy_view_post(self):
        rsp_post = responses.post(
            re.compile(settings.SSP_BASE_URL_V2 + "/some/path.*"),
            json={"key": "value"},
        )
        response = self.client.post(
            self.url, {"param": "value"}, headers=self.api_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"key": "value"})
        self.assertEqual(rsp_post.call_count, 1)


class TestEgisExternalProxyView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("egis-ext-proxy", args=["some/path"])

    def test_proxy_view_get(self):
        rsp_get = responses.get(
            re.compile(settings.SSP_BASE_URL_EXTERNAL + "/some/path.*"),
            json={"key": "value"},
        )
        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"key": "value"})
        self.assertEqual(rsp_get.call_count, 1)

    def test_proxy_view_post(self):
        rsp_post = responses.post(
            re.compile(settings.SSP_BASE_URL_EXTERNAL + "/some/path.*"),
            json={"key": "value"},
        )
        response = self.client.post(
            self.url, {"param": "value"}, headers=self.api_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"key": "value"})
        self.assertEqual(rsp_post.call_count, 1)


class TestWasteGuideView(ResponsesActivatedAPITestCase):
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
        self.assert_caching(self.url, rsp_get=self.rsp_get)


class TestAddressSearchByNameView(ResponsesActivatedAPITestCase):
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
        self.assert_caching(
            self.url, rsp_get=self.rsp_get, request_body={"query": "amstel"}
        )


class TestAddressSearchByCoordinateView(ResponsesActivatedAPITestCase):
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
        self.assert_caching(
            self.url, rsp_get=self.rsp_get, request_body={"lat": "50.7", "lon": "3.15"}
        )


class TestPollingStationsView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("elections-polling-stations")
        self.rsp_get = responses.get(
            re.compile(settings.POLLING_STATIONS_URL + ".*"),
            json=mock_data.POLLING_STATIONS_DATA,
        )

    def test_polling_stations_view(self):
        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        for polling_station in response.data:
            self.assertNotIn("reading_aid", polling_station.get("categories", []))
        self.assertEqual(self.rsp_get.call_count, 1)

    def test_cache(self):
        self.assert_caching(self.url, rsp_get=self.rsp_get)
