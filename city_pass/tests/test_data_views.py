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

        source_content_data = [{"passNumber": 1}, {"passNumber": 2}]
        mock_response.data = {"content": source_content_data, "status": "SUCCESS"}
        mock_get.return_value = mock_response

        result = self.client.get(self.api_url, headers=self.headers, follow=True)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data, source_content_data)

    def assert_source_api_error_was_logged_and_404_returned(
        self, mock_get, status_code, error_response
    ):
        mock_response = MagicMock()
        mock_response.status_code = status_code

        mock_response.data = error_response
        mock_get.return_value = mock_response

        with self.assertLogs("city_pass.views.data_views", level="ERROR") as cm:
            result = self.client.get(self.api_url, headers=self.headers, follow=True)

        expected_log_msg = str(error_response)
        self.assertTrue(any(expected_log_msg in message for message in cm.output))

        self.assertEqual(result.status_code, 404)
        self.assertContains(
            result,
            "Something went wrong during request to source data, see logs for more information",
            status_code=404,
        )

    @patch("city_pass.views.data_views.requests.get")
    def test_source_api_could_not_decrypt_admin_no(self, mock_get):
        self.assert_source_api_error_was_logged_and_404_returned(
            mock_get,
            400,
            {
                "content": "string",
                "code": 400,
                "status": "ERROR",
                "message": "Bad request: ApiError 005 - Could not decrypt url parameter administratienummerEncrypted'",
            },
        )

    @patch("city_pass.views.data_views.requests.get")
    def test_source_api_did_not_accept_api_key(self, mock_get):
        self.assert_source_api_error_was_logged_and_404_returned(
            mock_get,
            401,
            {
                "content": "string",
                "code": 401,
                "status": "ERROR",
                "message": "Api key ongeldig",
            },
        )
