from unittest.mock import Mock, patch

from django.conf import settings
from django.test import RequestFactory, TestCase, override_settings

from bridge.views.proxy_views import WasteGuideView


class TestWasteGuideView(TestCase):
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
