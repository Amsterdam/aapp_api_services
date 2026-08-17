from copy import deepcopy
from urllib.parse import urljoin

import responses
from django.conf import settings
from django.urls import reverse
from model_bakery import baker

from city_pass.models import Budget, PassData
from city_pass.tests.base_test import BaseCityPassTestCase
from city_pass.tests.mock_data import (
    aanbieding_transactions,
    budget_transactions,
    passes,
)


class BaseCityPassDataViewTestCase(BaseCityPassTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.headers = {**self.headers, "Access-Token": self.session.accesstoken.token}

    def build_source_api_url(self, path_key: str, suffix: str = "") -> str:
        return urljoin(
            settings.MIJN_AMS_API_DOMAIN,
            urljoin(settings.MIJN_AMS_API_PATHS[path_key], suffix),
        )

    def add_source_api_response(
        self,
        method: str,
        path_key: str,
        *,
        suffix: str = "",
        status: int = 200,
        payload: dict | None = None,
        content=None,
    ) -> None:
        response_payload = payload or {"content": content, "status": "SUCCESS"}
        responses.add(
            method,
            self.build_source_api_url(path_key, suffix),
            json=response_payload,
            status=status,
        )


class TestPassesView(BaseCityPassDataViewTestCase):
    api_url = reverse("city-pass-data-passes")

    def setUp(self) -> None:
        super().setUp()
        self.source_api_url = self.build_source_api_url(
            "PASSES", self.session.encrypted_adminstration_no
        )

    def add_passes_response(
        self, *, content=passes.MOCK_DATA, status=200, payload=None
    ):
        self.add_source_api_response(
            responses.GET,
            "PASSES",
            suffix=self.session.encrypted_adminstration_no,
            status=status,
            payload=payload,
            content=content,
        )

    def test_get_passes_successful(self):
        self.add_passes_response()

        result = self.client.get(self.api_url, headers=self.headers, follow=True)
        self.assertEqual(result.status_code, 200)

        # Check if transactionsKeyEncrypted was removed
        for pass_data_dict in result.data:
            self.assertIsNone(pass_data_dict.get("transactionsKeyEncrypted"))

        # Check if passNumber and transactionsKeyEncrypted were persisted
        pass_no_trans_key_dict = {
            str(x.get("passNumber")): x.get("transactionsKeyEncrypted")
            for x in passes.MOCK_DATA
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
        self.assertEqual(len(budgets), 3)
        self.assertTrue(Budget.objects.filter(code="2024_AMSTEG_4-9").exists())
        self.assertTrue(Budget.objects.filter(code="2024_AMSTEG_0-3").exists())
        self.assertTrue(Budget.objects.filter(code="2024_AMSTEG_PC").exists())

        # check if type field is present in the response and matches the original data
        for original_pass, response_pass in zip(
            passes.MOCK_DATA, result.data, strict=True
        ):
            self.assertIn("type", response_pass)
            self.assertEqual(original_pass.get("type"), response_pass.get("type"))

    def test_get_passes_successful_repeated(self):
        for _i in range(3):
            self.add_passes_response()

            result = self.client.get(self.api_url, headers=self.headers, follow=True)
            self.assertEqual(result.status_code, 200)

        # Check if budgets were persisted
        budgets = Budget.objects.all()
        self.assertEqual(len(budgets), 3)
        self.assertTrue(Budget.objects.filter(code="2024_AMSTEG_4-9").exists())
        self.assertTrue(Budget.objects.filter(code="2024_AMSTEG_0-3").exists())
        self.assertTrue(Budget.objects.filter(code="2024_AMSTEG_PC").exists())

    def assert_source_api_error_was_logged_and_500_returned(
        self, status_code: int, error_response: dict
    ):
        self.add_passes_response(status=status_code, payload=error_response)

        with self.assertLogs("city_pass.views.data_views", level="ERROR"):
            result = self.client.get(self.api_url, headers=self.headers, follow=True)

        self.assertEqual(result.status_code, 500)
        self.assertContains(
            result,
            "Something went wrong during request to source data, see logs for more information",
            status_code=500,
        )

    def test_source_api_could_not_decrypt_admin_no(self):
        self.assert_source_api_error_was_logged_and_500_returned(
            400,
            {
                "content": "string",
                "code": 400,
                "status": "ERROR",
                "message": "Bad request: ApiError 005 - Could not decrypt url parameter administratienummerEncrypted",
            },
        )

    def test_source_api_did_not_accept_api_key(self):
        self.assert_source_api_error_was_logged_and_500_returned(
            401,
            {
                "content": "string",
                "code": 401,
                "status": "ERROR",
                "message": "Api key ongeldig",
            },
        )

    def test_content_is_empty_list(self):
        self.add_passes_response(content=[])

        result = self.client.get(self.api_url, headers=self.headers, follow=True)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data, [])

    def test_content_is_invalid_format(self):
        self.add_passes_response(payload={"status": "FOOBAR"})

        result = self.client.get(self.api_url, headers=self.headers, follow=True)
        self.assertEqual(result.status_code, 500)

    def test_succeeds_after_retry(self):
        responses.add(
            responses.GET,
            self.source_api_url,
            json={"status": "ERROR", "message": "Internal Server Error"},
            status=500,
        )
        self.add_passes_response()

        result = self.client.get(self.api_url, headers=self.headers, follow=True)
        self.assertEqual(result.status_code, 200)

    def test_get_budget_transactions_succeeds_after_pass_refresh_with_new_pass_number(
        self,
    ):
        initial_pass = passes.MOCK_DATA[0]
        refreshed_pass = deepcopy(initial_pass)
        refreshed_pass["passNumber"] = 6011013119999
        refreshed_pass["passNumberComplete"] = "6064366011013119999"
        refreshed_pass["transactionsKeyEncrypted"] = "updated-encrypted-key"

        self.add_passes_response(content=[initial_pass])
        self.add_source_api_response(
            responses.GET,
            "BUDGET_TRANSACTIONS",
            suffix=initial_pass["transactionsKeyEncrypted"],
            content=budget_transactions.MOCK_DATA,
        )
        self.add_passes_response(content=[refreshed_pass])
        self.add_source_api_response(
            responses.GET,
            "BUDGET_TRANSACTIONS",
            suffix=refreshed_pass["transactionsKeyEncrypted"],
            content=budget_transactions.MOCK_DATA,
        )

        first_passes_result = self.client.get(
            self.api_url,
            headers=self.headers,
            follow=True,
        )
        self.assertEqual(first_passes_result.status_code, 200)

        first_budget_transactions_result = self.client.get(
            reverse("city-pass-data-budget-transactions"),
            headers=self.headers,
            data={"passNumber": str(initial_pass["passNumber"])},
            follow=True,
        )
        self.assertEqual(first_budget_transactions_result.status_code, 200)

        refreshed_passes_result = self.client.get(
            self.api_url,
            headers=self.headers,
            follow=True,
        )
        self.assertEqual(refreshed_passes_result.status_code, 200)

        refreshed_budget_transactions_result = self.client.get(
            reverse("city-pass-data-budget-transactions"),
            headers=self.headers,
            data={"passNumber": str(refreshed_pass["passNumber"])},
            follow=True,
        )
        self.assertEqual(refreshed_budget_transactions_result.status_code, 200)
        self.assertTrue(
            PassData.objects.filter(
                session=self.session,
                pass_number=str(refreshed_pass["passNumber"]),
                encrypted_transaction_key=refreshed_pass["transactionsKeyEncrypted"],
            ).exists()
        )


class BaseTransactionsViewTestCase(BaseCityPassDataViewTestCase):
    api_url = ""
    source_api_content = []
    source_api_path_key = ""
    __test__ = (
        False  # Skip this class in test discovery and only use it as a base class
    )

    def setUp(self) -> None:
        super().setUp()
        self.pass_number = "6011013116525"
        self.pass_data = baker.make(
            PassData,
            session=self.session,
            pass_number=self.pass_number,
            encrypted_transaction_key="encrypted-transaction-key",
        )

    def add_transactions_response(self, *, content=None, payload=None):
        self.add_source_api_response(
            responses.GET,
            self.source_api_path_key,
            suffix=self.pass_data.encrypted_transaction_key,
            payload=payload,
            content=self.source_api_content if content is None else content,
        )

    def test_get_transactions_successful(self):
        self.add_transactions_response()

        result = self.client.get(
            self.api_url,
            headers=self.headers,
            data={"passNumber": self.pass_number},
            follow=True,
        )
        self.assertEqual(200, result.status_code)

    def test_get_transactions_no_pass_number(self):
        result = self.client.get(self.api_url, headers=self.headers, follow=True)
        self.assertEqual(400, result.status_code)

    def test_get_transactions_unknown_pass_number(self):
        result = self.client.get(
            self.api_url,
            headers=self.headers,
            data={"passNumber": "12345"},
            follow=True,
        )
        self.assertEqual(500, result.status_code)

    def test_content_is_invalid_format(self):
        self.add_transactions_response(payload={"status": "FOOBAR"})

        result = self.client.get(
            self.api_url,
            headers=self.headers,
            data={"passNumber": self.pass_number},
            follow=True,
        )
        self.assertEqual(500, result.status_code)


class TestBudgetTransactionsViews(BaseTransactionsViewTestCase):
    api_url = reverse("city-pass-data-budget-transactions")
    source_api_content = budget_transactions.MOCK_DATA
    source_api_path_key = "BUDGET_TRANSACTIONS"
    __test__ = True

    def test_content_is_empty_list(self):
        self.add_transactions_response(content=[])

        result = self.client.get(
            self.api_url,
            headers=self.headers,
            data={"passNumber": self.pass_number},
            follow=True,
        )
        self.assertEqual(200, result.status_code)
        self.assertEqual(result.data, [])


class TestAanbiedingTransactionsViews(BaseTransactionsViewTestCase):
    api_url = reverse("city-pass-data-aanbieding-transactions")
    source_api_content = aanbieding_transactions.MOCK_DATA
    source_api_path_key = "AANBIEDING_TRANSACTIONS"
    __test__ = True

    def test_content_is_empty_dict(self):
        content = {
            "discountAmountTotal": 0,
            "discountAmountTotalFormatted": "€0,00",
            "transactions": [],
        }
        self.add_transactions_response(content=content)

        result = self.client.get(
            self.api_url,
            headers=self.headers,
            data={"passNumber": self.pass_number},
            follow=True,
        )
        self.assertEqual(200, result.status_code)
        self.assertEqual(result.data, content)


class TestPassBlockView(BaseCityPassDataViewTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.pass_number = "6011013116525"
        self.pass_data = baker.make(
            PassData,
            session=self.session,
            pass_number=self.pass_number,
            encrypted_transaction_key="block-encrypted-transaction-key",
        )

    def test_block_pass_successful(self):
        self.add_source_api_response(
            responses.POST,
            "PASS_BLOCK",
            suffix=self.pass_data.encrypted_transaction_key,
            content="foobar",
        )

        url = reverse("city-pass-data-pass-block", args=[self.pass_number])
        result = self.client.put(
            url,
            headers=self.headers,
            follow=True,
        )
        self.assertEqual(200, result.status_code)

    def test_block_pass_unknown_pass_number(self):
        url = reverse("city-pass-data-pass-block", args=[123])
        result = self.client.put(
            url,
            headers=self.headers,
            follow=True,
        )
        self.assertEqual(500, result.status_code)
