from unittest.mock import MagicMock, patch

from django.test import override_settings

from city_pass.tests.base_test import BaseCityPassTestCase


class TestPassesView(BaseCityPassTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.override = override_settings(
            MIJN_AMS_API_DOMAIN="http://mijn-ams-mock-domain/",
            MIJN_AMS_API_PATHS={"PASSES": "/mock-passes-path/"},
            MIJN_AMS_API_KEY="mijn-ams-mock-api-key",
        )
        self.override.enable()
        self.addCleanup(self.override.disable)

        self.mock_session = MagicMock()
        self.mock_session.encrypted_adminstration_no = "mock_admin_no"
        self.patcher_authenticate = patch(
            "city_pass.views.data_views.authentication.authenticate_access_token"
        )
        self.mock_authenticate = self.patcher_authenticate.start()
        self.mock_authenticate.return_value = (self.mock_session, None)

        self.api_url = "/city-pass/api/v1/data/passes"

    @patch("city_pass.views.data_views.requests.get")
    def test_get_passes_successful(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        # TODO: add mock data
        mock_response.data = None
        mock_get.return_value = mock_response

        result = self.client.get(self.api_url, headers=self.headers, follow=True)
        self.assertEqual(result.status_code, 200)

    @patch("city_pass.views.data_views.requests.get")
    def test_502_from_source_returns_404_status(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 502
        mock_get.return_value = mock_response

        result = self.client.get(self.api_url, headers=self.headers, follow=True)
        self.assertEqual(result.status_code, 404)
