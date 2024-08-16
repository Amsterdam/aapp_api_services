import json
from unittest.mock import patch

from django.test import override_settings
from requests import Response

from city_pass.models import PassData, Session
from city_pass.tests.base_test import BaseCityPassTestCase
from model_bakery import baker

class TestPassesView(BaseCityPassTestCase):
    mock_response_data = [
        {
            "id": "201604",
            "owner": {
                "firstname": "Chelsea",
                "lastname": "Innocent",
                "initials": "C",
            },
            "dateEnd": "2025-07-31T21:59:59.000Z",
            "dateEndFormatted": "31 juli 2025",
            "budgets": [
                {
                    "title": "24/25 Kindtegoed 4 tm 9 jaar",
                    "description": "",
                    "code": "2024_AMSTEG_4-9",
                    "budgetAssigned": 241,
                    "budgetAssignedFormatted": "€241,00",
                    "budgetBalance": 241,
                    "budgetBalanceFormatted": "€241,00",
                    "dateEnd": "2025-07-31T21:59:59.000Z",
                    "dateEndFormatted": "31 juli 2025",
                }
            ],
            "balanceFormatted": "€241,00",
            "passNumber": 6011013116525,
            "passNumberComplete": "6064366011013116525",
            "transactionsKeyEncrypted": "NU-5XEzItQQkg7P17RT813RjDSQn8YH9Uj30sSRaO5lkP4zg0J2wXAYLu8s9xtj9",
        },
        {
            "id": "201605",
            "owner": {"firstname": "Mini", "lastname": "Klaproos", "initials": "M"},
            "dateEnd": "2025-07-31T21:59:59.000Z",
            "dateEndFormatted": "31 juli 2025",
            "budgets": [
                {
                    "title": "24/25 Kindtegoed 0 tm 3 jaar",
                    "description": "",
                    "code": "2024_AMSTEG_0-3",
                    "budgetAssigned": 125,
                    "budgetAssignedFormatted": "€125,00",
                    "budgetBalance": 125,
                    "budgetBalanceFormatted": "€125,00",
                    "dateEnd": "2025-07-31T21:59:59.000Z",
                    "dateEndFormatted": "31 juli 2025",
                }
            ],
            "balanceFormatted": "€125,00",
            "passNumber": 6011013117242,
            "passNumberComplete": "6064366011013117242",
            "transactionsKeyEncrypted": "a24WShplCZ7MRAVSMDyvi0kMuOUNQBsPNC8b4HePJl3iOfOPeg9oVOZ3PkpesC3c",
        },
    ]

    def setUp(self) -> None:
        super().setUp()
        self.override = override_settings(
            MIJN_AMS_API_DOMAIN="http://mijn-ams-mock-domain/",
            MIJN_AMS_API_PATHS={"PASSES": "/mock-passes-path/"},
            MIJN_AMS_API_KEY="mijn-ams-mock-api-key",
        )
        self.override.enable()
        self.addCleanup(self.override.disable)

        self.mock_session = Session.objects.create()
        self.mock_session.encrypted_adminstration_no = "mock_admin_no"
        self.patcher_authenticate = patch(
            "city_pass.views.data_views.authentication.AccessTokenAuthentication.authenticate"
        )
        self.mock_authenticate = self.patcher_authenticate.start()
        self.mock_authenticate.return_value = (self.mock_session, None)

        self.api_url = "/city-pass/api/v1/data/passes"

    @patch("city_pass.views.data_views.requests.get")
    def test_get_passes_successful(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = json.dumps(
            {"content": self.mock_response_data, "status": "SUCCESS"}
        ).encode("utf-8")
        mock_get.return_value = mock_response

        result = self.client.get(self.api_url, headers=self.headers, follow=True)
        self.assertEqual(result.status_code, 200)

        # Check if transactionsKeyEncrypted was removed
        for pass_data_dict in result.data:
            self.assertIsNone(pass_data_dict.get("transactionsKeyEncrypted"))

        # Check if passNumber and transactionsKeyEncrypted were persisted
        pass_no_trans_key_dict = {
            str(x.get("passNumber")): x.get("transactionsKeyEncrypted")
            for x in self.mock_response_data
        }
        for pass_data_dict in result.data:
            pass_data_obj = PassData.objects.get(
                pass_number=pass_data_dict.get("passNumber")
            )
            self.assertEqual(
                pass_data_obj.encrypted_transaction_key,
                pass_no_trans_key_dict.get(pass_data_obj.pass_number),
            )

    def assert_source_api_error_was_logged_and_404_returned(
        self, mock_get, status_code: int, error_response: dict
    ):
        mock_response = Response()
        mock_response.status_code = status_code

        encoded_error_response = json.dumps(error_response).encode("utf-8")
        mock_response._content = encoded_error_response
        mock_get.return_value = mock_response

        with self.assertLogs("city_pass.views.data_views", level="ERROR") as cm:
            result = self.client.get(self.api_url, headers=self.headers, follow=True)

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
                "message": "Bad request: ApiError 005 - Could not decrypt url parameter administratienummerEncrypted",
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

    @patch("city_pass.views.data_views.requests.get")
    def test_content_is_empty_list(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 200

        mock_response._content = json.dumps(
            {"content": [], "status": "SUCCESS"}
        ).encode("utf-8")
        mock_get.return_value = mock_response

        result = self.client.get(self.api_url, headers=self.headers, follow=True)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data, [])

    @patch("city_pass.views.data_views.requests.get")
    def test_content_is_invalid_format(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 200

        mock_response._content = json.dumps({"status": "FOOBAR"}).encode("utf-8")
        mock_get.return_value = mock_response

        result = self.client.get(self.api_url, headers=self.headers, follow=True)
        self.assertEqual(result.status_code, 500)


@patch("city_pass.views.data_views.requests.get")
class TestBudgetTransactionsViews(BaseCityPassTestCase):
    mock_response_data = [
        {
            "id": "201604",
            "title": "Hema",
            "amount": 9.95,
            "amountFormatted": "€9,95",
            "datePublished": "2025-07-31T21:59:59.000Z",
            "datePublishedFormatted": "31 juli 2025",
            "budget": "24/25 Kindtegoed 4 tm 9 jaar",
            "budgetCode": "2024_AMSTEG_4-9",
        },
        {
            "id": "201605",
            "title": "Aktiesport",
            "amount": 4.95,
            "amountFormatted": "€4,95",
            "datePublished": "2025-07-31T21:59:59.000Z",
            "datePublishedFormatted": "31 juli 2025",
            "budget": "24/25 Kindtegoed 0 tm 3 jaar",
            "budgetCode": "2024_AMSTEG_0-3",
        },
        {
            "id": "201606",
            "title": "AFC Ijburg",
            "amount": 182.95,
            "amountFormatted": "€182,95",
            "datePublished": "2025-07-28T21:59:59.000Z",
            "datePublishedFormatted": "28 juli 2025",
            "budget": "24/25 Kindtegoed 0 tm 3 jaar",
            "budgetCode": "2024_AMSTEG_0-3",
        },
    ]

    def setUp(self) -> None:
        super().setUp()
        self.override = override_settings(
            MIJN_AMS_API_DOMAIN="http://mijn-ams-mock-domain/",
            MIJN_AMS_API_PATHS={"BUDGET_TRANSACTIONS": "/mock-budget-transactions-path/"},
            MIJN_AMS_API_KEY="mijn-ams-mock-api-key",
        )
        self.override.enable()
        self.addCleanup(self.override.disable)

        self.mock_session = Session.objects.create()
        self.mock_session.encrypted_adminstration_no = "mock_admin_no"
        self.patcher_authenticate = patch(
            "city_pass.views.data_views.authentication.AccessTokenAuthentication.authenticate"
        )
        self.mock_authenticate = self.patcher_authenticate.start()
        self.mock_authenticate.return_value = (self.mock_session, None)

        self.api_url = "/city-pass/api/v1/data/budget-transactions"

        self.pass_number = "6011013116525"
        self.pass_data = baker.make(PassData, session=self.mock_session, pass_number=self.pass_number)

    def test_get_budget_transactions_successful(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = json.dumps(
            {"content": self.mock_response_data, "status": "SUCCESS"}
        ).encode("utf-8")
        mock_get.return_value = mock_response

        result = self.client.get(
            self.api_url,
            headers=self.headers,
            query_params={"passNumber": self.pass_number},
            follow=True
        )
        self.assertEqual(200, result.status_code)

    def test_get_budget_transactions_no_pass_number(self, _):
        result = self.client.get(
            self.api_url,
            headers=self.headers,
            follow=True
        )
        self.assertEqual(400, result.status_code)

    def test_get_budget_transactions_unknown_pass_number(self, _):
        result = self.client.get(
            self.api_url,
            headers=self.headers,
            query_params={"passNumber": "12345"},
            follow=True
        )
        self.assertEqual(404, result.status_code)

    # def test_content_is_empty_list(self, mock_get):
    #     mock_response = Response()
    #     mock_response.status_code = 200
    #
    #     mock_response._content = json.dumps(
    #         {"content": [], "status": "SUCCESS"}
    #     ).encode("utf-8")
    #     mock_get.return_value = mock_response
    #
    #     result = self.client.get(
    #         self.api_url,
    #         headers=self.headers,
    #         query_params={"passNumber": self.pass_number},
    #         follow=True
    #     )
    #     self.assertEqual(200, result.status_code)
    #     self.assertEqual(result.data, [])
    #
    # def test_content_is_invalid_format(self, mock_get):
    #     mock_response = Response()
    #     mock_response.status_code = 200
    #
    #     mock_response._content = json.dumps({"status": "FOOBAR"}).encode("utf-8")
    #     mock_get.return_value = mock_response
    #
    #     result = self.client.get(
    #         self.api_url,
    #         headers=self.headers,
    #         query_params={"passNumber": self.pass_number},
    #         follow=True
    #     )
    #     self.assertEqual(500, result.status_code)
