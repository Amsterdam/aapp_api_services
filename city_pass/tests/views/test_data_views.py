import json
from unittest.mock import patch

from django.urls import reverse
from model_bakery import baker
from requests import Response

from city_pass.models import Budget, PassData
from city_pass.tests import mock_data
from city_pass.tests.base_test import BaseCityPassTestCase


class TestPassesView(BaseCityPassTestCase):
    api_url = reverse("city-pass-data-passes")

    def setUp(self) -> None:
        super().setUp()
        self.headers = {**self.headers, "Access-Token": self.session.accesstoken.token}

    @patch("city_pass.views.data_views.requests.request")
    def test_get_passes_successful(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = json.dumps(
            {"content": mock_data.passes, "status": "SUCCESS"}
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
            for x in mock_data.passes
        }
        for pass_data_dict in result.data:
            pass_data_obj = PassData.objects.get(
                pass_number=pass_data_dict.get("passNumber")
            )
            self.assertEqual(
                pass_data_obj.encrypted_transaction_key,
                pass_no_trans_key_dict.get(pass_data_obj.pass_number),
            )

        # Check if budgets were persisted
        budgets = Budget.objects.all()
        self.assertEqual(len(budgets), 2)
        self.assertTrue(Budget.objects.filter(code="2024_AMSTEG_4-9").exists())
        self.assertTrue(Budget.objects.filter(code="2024_AMSTEG_0-3").exists())

    def assert_source_api_error_was_logged_and_500_returned(
        self, mock_get, status_code: int, error_response: dict
    ):
        mock_response = Response()
        mock_response.status_code = status_code

        encoded_error_response = json.dumps(error_response).encode("utf-8")
        mock_response._content = encoded_error_response
        mock_get.return_value = mock_response

        with self.assertLogs("city_pass.views.data_views", level="ERROR"):
            result = self.client.get(self.api_url, headers=self.headers, follow=True)

        self.assertEqual(result.status_code, 500)
        self.assertContains(
            result,
            "Something went wrong during request to source data, see logs for more information",
            status_code=500,
        )

    @patch("city_pass.views.data_views.requests.request")
    def test_source_api_could_not_decrypt_admin_no(self, mock_get):
        self.assert_source_api_error_was_logged_and_500_returned(
            mock_get,
            400,
            {
                "content": "string",
                "code": 400,
                "status": "ERROR",
                "message": "Bad request: ApiError 005 - Could not decrypt url parameter administratienummerEncrypted",
            },
        )

    @patch("city_pass.views.data_views.requests.request")
    def test_source_api_did_not_accept_api_key(self, mock_get):
        self.assert_source_api_error_was_logged_and_500_returned(
            mock_get,
            401,
            {
                "content": "string",
                "code": 401,
                "status": "ERROR",
                "message": "Api key ongeldig",
            },
        )

    @patch("city_pass.views.data_views.requests.request")
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

    @patch("city_pass.views.data_views.requests.request")
    def test_content_is_invalid_format(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 200

        mock_response._content = json.dumps({"status": "FOOBAR"}).encode("utf-8")
        mock_get.return_value = mock_response

        result = self.client.get(self.api_url, headers=self.headers, follow=True)
        self.assertEqual(result.status_code, 500)

    @patch("city_pass.views.data_views.requests.request")
    def test_succeeds_after_retry(self, mock_get):
        # Simulate a 500 error on the first request
        mock_response_1 = Response()
        mock_response_1.status_code = 500
        mock_response_1._content = json.dumps(
            {"status": "ERROR", "message": "Internal Server Error"}
        ).encode("utf-8")

        # Simulate a successful response on the second request
        mock_response_2 = Response()
        mock_response_2.status_code = 200
        mock_response_2._content = json.dumps(
            {"content": mock_data.passes, "status": "SUCCESS"}
        ).encode("utf-8")

        mock_get.side_effect = [mock_response_1, mock_response_2]

        result = self.client.get(self.api_url, headers=self.headers, follow=True)
        self.assertEqual(result.status_code, 200)


@patch("city_pass.views.data_views.requests.request")
class BaseAbstractTransactionsViews(BaseCityPassTestCase):
    api_url = ""
    mock_data = []
    __test__ = (
        False  # Skip this class in test discovery and only use it as a base class
    )

    def setUp(self) -> None:
        super().setUp()
        self.headers = {**self.headers, "Access-Token": self.session.accesstoken.token}
        self.pass_number = "6011013116525"
        self.pass_data = baker.make(
            PassData, session=self.session, pass_number=self.pass_number
        )

    def test_get_transactions_successful(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = json.dumps(
            {"content": self.mock_data, "status": "SUCCESS"}
        ).encode("utf-8")
        mock_get.return_value = mock_response

        result = self.client.get(
            self.api_url,
            headers=self.headers,
            data={"passNumber": self.pass_number},
            follow=True,
        )
        self.assertEqual(200, result.status_code)

    def test_get_transactions_no_pass_number(self, _):
        result = self.client.get(self.api_url, headers=self.headers, follow=True)
        self.assertEqual(400, result.status_code)

    def test_get_transactions_unknown_pass_number(self, _):
        result = self.client.get(
            self.api_url,
            headers=self.headers,
            data={"passNumber": "12345"},
            follow=True,
        )
        self.assertEqual(500, result.status_code)

    def test_content_is_invalid_format(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 200

        mock_response._content = json.dumps({"status": "FOOBAR"}).encode("utf-8")
        mock_get.return_value = mock_response

        result = self.client.get(
            self.api_url,
            headers=self.headers,
            data={"passNumber": self.pass_number},
            follow=True,
        )
        self.assertEqual(500, result.status_code)


class TestBudgetTransactionsViews(BaseAbstractTransactionsViews):
    api_url = reverse("city-pass-data-budget-transactions")
    mock_data = mock_data.budget_transactions
    __test__ = True

    @patch("city_pass.views.data_views.requests.request")
    def test_content_is_empty_list(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 200

        mock_response._content = json.dumps(
            {"content": [], "status": "SUCCESS"}
        ).encode("utf-8")
        mock_get.return_value = mock_response

        result = self.client.get(
            self.api_url,
            headers=self.headers,
            data={"passNumber": self.pass_number},
            follow=True,
        )
        self.assertEqual(200, result.status_code)
        self.assertEqual(result.data, [])


class TestAanbiedingTransactionsViews(BaseAbstractTransactionsViews):
    api_url = reverse("city-pass-data-aanbieding-transactions")
    mock_data = mock_data.aanbieding_transactions
    __test__ = True

    @patch("city_pass.views.data_views.requests.request")
    def test_content_is_empty_dict(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 200

        content = {
            "discountAmountTotal": 0,
            "discountAmountTotalFormatted": "€0,00",
            "transactions": [],
        }
        mock_response._content = json.dumps(
            {"content": content, "status": "SUCCESS"}
        ).encode("utf-8")
        mock_get.return_value = mock_response

        result = self.client.get(
            self.api_url,
            headers=self.headers,
            data={"passNumber": self.pass_number},
            follow=True,
        )
        self.assertEqual(200, result.status_code)
        self.assertEqual(result.data, content)


class TestPassBlockView(BaseCityPassTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.headers = {**self.headers, "Access-Token": self.session.accesstoken.token}
        self.pass_number = "6011013116525"
        self.pass_data = baker.make(
            PassData, session=self.session, pass_number=self.pass_number
        )

    @patch("city_pass.views.data_views.requests.request")
    def test_block_pass_successful(self, mock_post):
        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = json.dumps(
            {"content": "foobar", "status": "SUCCESS"}
        ).encode("utf-8")
        mock_post.return_value = mock_response

        url = reverse("city-pass-data-pass-block", args=[self.pass_number])
        result = self.client.post(
            url,
            headers=self.headers,
            data={"passNumber": self.pass_number},
            follow=True,
        )
        self.assertEqual(200, result.status_code)
