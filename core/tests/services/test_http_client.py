import responses
from django.conf import settings
from django.test import TestCase, override_settings

from core.services.internal_http_client import (
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_READ_TIMEOUT,
    DEFAULT_RETRIES,
    RETRY_ON_STATUS_CODES,
    InternalServiceSession,
)


class TestInternalServiceSession(TestCase):
    """Test the InternalServiceSession with responses mocking."""

    @responses.activate
    def test_default_timeout_applied(self):
        """Test that the default timeout is applied to the request."""
        responses.get(
            "https://api.example.com/test",
            json={"status": "success", "data": "test"},
            status=200,
        )
        session = InternalServiceSession()
        session.request("GET", "https://api.example.com/test")
        mocked_request = responses.calls[0].request
        self.assertEqual(
            mocked_request.req_kwargs["timeout"],
            (DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT),
        )

    @responses.activate
    def test_request_with_custom_timeout(self):
        """Test that the request method uses the timeout parameter."""
        responses.get(
            "https://api.example.com/test",
            json={"status": "success", "data": "test"},
            status=200,
        )
        session = InternalServiceSession()
        session.request("GET", "https://api.example.com/test", timeout=1)
        mocked_request = responses.calls[0].request
        self.assertEqual(mocked_request.req_kwargs["timeout"], 1)

    @responses.activate
    def test_get_request_mocked(self):
        """Test that responses intercepts GET requests from InternalServiceSession."""
        # Mock the response - responses will intercept the actual HTTP request
        responses.get(
            "https://api.example.com/test",
            json={"status": "success", "data": "test"},
            status=200,
        )

        client = InternalServiceSession()
        response = client.get("https://api.example.com/test")

        # Verify the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "data": "test"})

        # Verify that responses intercepted the call
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, "https://api.example.com/test")
        self.assertEqual(responses.calls[0].request.method, "GET")

    @responses.activate
    @override_settings(
        API_KEY_HEADER="X-Api-Key", API_KEYS="test-api-key,other-api-key"
    )
    def test_get_request_with_headers(self):
        """Test that the client passes the headers to the request."""
        responses.get(
            "https://api.example.com/test",
            json={"status": "success", "data": "test"},
            status=200,
        )

        client = InternalServiceSession()
        response = client.get(
            "https://api.example.com/test", headers={"X-Test": "test"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "data": "test"})
        self.assertEqual(responses.calls[0].request.headers["X-Test"], "test")
        self.assertEqual(
            responses.calls[0].request.headers[settings.API_KEY_HEADER],
            settings.API_KEYS.split(",")[0],
        )

    @responses.activate
    def test_max_retries_reached(self):
        url = "https://api.example.com/test"

        # Prepare more requests than retries to test the retry logic
        for _ in range(DEFAULT_RETRIES * 2):
            responses.get(url, status=502)

        session = InternalServiceSession()
        response = session.get(url)

        self.assertEqual(response.status_code, 502)
        # Total calls should be initial request + retries
        self.assertEqual(len(responses.calls), 1 + DEFAULT_RETRIES)

    @responses.activate
    def mock_retry_on_status_codes(self, retry_status_code: int):
        url = "https://api.example.com/test"

        responses.get(url, status=retry_status_code)
        responses.get(url, status=200)

        session = InternalServiceSession()
        response = session.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(responses.calls), 2)

    def test_retry_on_status_codes(self):
        for retry_status_code in RETRY_ON_STATUS_CODES:
            self.mock_retry_on_status_codes(retry_status_code)

    @responses.activate
    def test_retry_not_on_4xx_status_codes(self):
        url = "https://api.example.com/test"

        responses.get(url, status=400)
        responses.get(url, status=200)

        session = InternalServiceSession()
        response = session.get(url)

        # Request should not retry and return 400 status code
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(responses.calls), 1)
