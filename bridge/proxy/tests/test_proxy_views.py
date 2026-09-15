import json
import re
from types import SimpleNamespace
from unittest.mock import Mock, patch

import freezegun
import responses
from django.conf import settings
from django.urls import reverse
from requests.exceptions import RequestException

from bridge.proxy.tests import mock_data
from bridge.proxy.views import AfvalscheidingswijzerView
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


class TestAddressPostalAreaByCoordinateView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("address-postal-area-by-coordinate")

    @patch("bridge.proxy.views.load_postal_area_shapes")
    def test_success(self, patched_load_data):
        patched_load_data.return_value = mock_data.MOCK_POSTAL_AREA_SHAPES

        response = self.client.get(
            self.url,
            {"lat": "52.37148701", "lon": "4.85838607"},
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"postal_area": "1056"})

    @patch("bridge.proxy.views.load_postal_area_shapes")
    def test_not_found(self, patched_load_data):
        patched_load_data.return_value = mock_data.MOCK_POSTAL_AREA_SHAPES
        response = self.client.get(
            self.url,
            {"lat": "52.4574236", "lon": "4.6111981"},
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 404)


class TestAfvalscheidingswijzerView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("afvalscheidingswijzer")
        self.expected_payload = json.loads(
            mock_data.AFVALSCHEIDINGSWIJZER.splitlines()[1][2:]
        )
        self.expected_error = {"detail": "Upstream afvalscheidingswijzer error"}

    def _post_plain_text(self, url=None):
        return self.client.generic(
            "POST",
            url or self.url,
            b"potgrond",
            content_type="text/plain",
            headers=self.api_headers,
        )

    def test_success(self):
        upstream_response = Mock(
            status_code=201,
            text=mock_data.AFVALSCHEIDINGSWIJZER,
        )

        with patch(
            "bridge.proxy.views.requests.post", return_value=upstream_response
        ) as patched_post:
            response = AfvalscheidingswijzerView().post(
                SimpleNamespace(body=b"potgrond")
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, self.expected_payload)
        patched_post.assert_called_once_with(
            settings.AFVALSCHEIDINGSWIJZER_URL,
            data=b"potgrond",
            headers={
                "content-type": "text/plain;charset=UTF-8",
                "next-action": "40f8fc5dcb243472b32eb5cb1040d8e6e896f79498",
                "origin": "https://www.afvalscheidingswijzer.nl",
                "user-agent": "Mozilla/5.0",
            },
            timeout=5,
        )

    def test_success_response_is_json(self):
        responses.post(
            settings.AFVALSCHEIDINGSWIJZER_URL,
            body=mock_data.AFVALSCHEIDINGSWIJZER,
            content_type="text/x-component",
            status=201,
        )

        response = self._post_plain_text()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, self.expected_payload)
        self.assertTrue(response["Content-Type"].startswith("application/json"))

    @patch("bridge.proxy.views.requests.post", side_effect=RequestException)
    def test_returns_502_on_upstream_failure(self, patched_post):
        response = self._post_plain_text()

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data, self.expected_error)
        patched_post.assert_called_once()

    def test_returns_502_when_payload_line_is_missing(self):
        responses.post(
            settings.AFVALSCHEIDINGSWIJZER_URL,
            body='0:{"meta":true}\n',
            content_type="text/x-component",
            status=200,
        )

        response = self._post_plain_text()

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data, self.expected_error)

    def test_returns_502_when_multiple_payload_lines_are_present(self):
        responses.post(
            settings.AFVALSCHEIDINGSWIJZER_URL,
            body='0:{"meta":true}\n1:{"first":true}\n1:{"second":true}\n',
            content_type="text/x-component",
            status=200,
        )

        response = self._post_plain_text()

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data, self.expected_error)

    def test_returns_502_when_payload_line_contains_invalid_json(self):
        responses.post(
            settings.AFVALSCHEIDINGSWIJZER_URL,
            body='0:{"meta":true}\n1:{invalid json}\n',
            content_type="text/x-component",
            status=200,
        )

        response = self._post_plain_text()

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data, self.expected_error)

    def test_returns_502_when_payload_is_not_a_json_object(self):
        responses.post(
            settings.AFVALSCHEIDINGSWIJZER_URL,
            body='0:{"meta":true}\n1:[1,2,3]\n',
            content_type="text/x-component",
            status=200,
        )

        response = self._post_plain_text()

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.data, self.expected_error)

    def test_post_only(self):
        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 405)

    def test_trailing_slash_behavior(self):
        response = self._post_plain_text(url=f"{self.url}/")

        self.assertEqual(response.status_code, 404)


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


class TestHealthCheckView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("health-check")

    def test_health_check(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class TestServerTimeView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("server-time")

    @freezegun.freeze_time("2026-05-10 12:00:00")
    def test_server_time_view(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        # check that the returned server time matches the frozen time in ISO format with timezone
        self.assertEqual(response.data["server_time"], "2026-05-10T14:00:00+02:00")
