from unittest.mock import Mock, patch

from django.conf import settings
from django.core.cache import cache
from django.test import RequestFactory, override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from bridge.proxy.views import WasteGuideView


class TestWasteGuideView(APITestCase):
    def setUp(self):
        # flush cache before every test run
        cache.clear()

    @override_settings(
        WASTE_GUIDE_URL="http://example.com/wasteguide",
        WASTE_GUID_API_KEY="test_api_key",
    )
    @patch("requests.request")
    def test_waste_guide_view(self, mock_request):
        # Mock the response from the external API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # Call the view
        factory = RequestFactory()
        request = factory.get("/waste-guide/api/v1/search")
        WasteGuideView.as_view()(request)

        # Assert that the external request was called with the X-Api-Key
        mock_request.assert_called_once_with(
            method="GET",
            url=settings.WASTE_GUIDE_URL,
            headers={"X-Api-Key": settings.WASTE_GUID_API_KEY},
            params=request.GET,
        )

    @patch("bridge.proxy.views.requests.request")
    def test_cache(self, mock_request):
        url = reverse("waste-guide-search")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        # First call
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # The request and the headers are cached both as separate keys
        self.assertEqual(len(cache.keys("*")), 2)
        mock_request.assert_called_once()

        # Second call
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(cache.keys("*")), 2)
        mock_request.assert_called_once()  # The request should not be called again
