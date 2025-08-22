import responses
from django.conf import settings
from django.test import TestCase, override_settings

from core.services.internal_http_client import (
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_READ_TIMEOUT,
    InternalServiceHttpClient,
    TimeoutSession,
)


class TestTimeoutSession(TestCase):
    """Test the TimeoutSession class."""

    @responses.activate
    def test_default_timeout_applied(self):
        """Test that the default timeout is applied to the request."""
        responses.get(
            "https://api.example.com/test",
            json={"status": "success", "data": "test"},
            status=200,
        )
        session = TimeoutSession()
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
        session = TimeoutSession()
        session.request("GET", "https://api.example.com/test", timeout=1)
        mocked_request = responses.calls[0].request
        self.assertEqual(mocked_request.req_kwargs["timeout"], 1)


class TestInternalServiceHttpClient(TestCase):
    """Test the InternalServiceHttpClient with responses mocking."""

    @responses.activate
    def test_get_request_mocked(self):
        """Test that responses intercepts GET requests from InternalServiceHttpClient."""
        # Mock the response - responses will intercept the actual HTTP request
        responses.get(
            "https://api.example.com/test",
            json={"status": "success", "data": "test"},
            status=200,
        )

        client = InternalServiceHttpClient()
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

        client = InternalServiceHttpClient()
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
    def test_all_methods_are_proxied(self):
        """Test that all methods are proxied to the session."""
        responses.get(
            "http://test/get",
            status=200,
        )
        responses.post(
            "http://test/post",
            status=200,
        )
        responses.patch(
            "http://test/patch",
            status=200,
        )
        responses.delete(
            "http://test/delete",
            status=200,
        )
        responses.put(
            "http://test/put",
            status=200,
        )

        client = InternalServiceHttpClient()
        client.get("http://test/get")
        client.post("http://test/post")
        client.patch("http://test/patch")
        client.delete("http://test/delete")
        client.put("http://test/put")

        self.assertEqual(responses.calls[0].request.method, "GET")
        self.assertEqual(responses.calls[1].request.method, "POST")
        self.assertEqual(responses.calls[2].request.method, "PATCH")
        self.assertEqual(responses.calls[3].request.method, "DELETE")
        self.assertEqual(responses.calls[4].request.method, "PUT")
