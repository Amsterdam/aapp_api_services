import httpx
import respx
from django.urls import reverse

from bridge.parking.services.ssp import SSPEndpointExternal
from bridge.parking.tests.mock_data import (
    transactions,
)
from bridge.parking.tests.mock_data_external import (
    wallet_transaction,
    wallet_transaction_confirm,
)
from bridge.parking.tests.views.base_ssp_view import BaseSSPTestCase
from bridge.parking.views.transaction_views import (
    TransactionsBalanceView,
    TransactionsListView,
)


class TestTransactionsRechargeView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-balance")

        self.test_payload = {
            "balance": {"amount": "10"},
            "payment_type": "IDEAL",
            "locale": "nl",
        }
        self.test_response = wallet_transaction.MOCK_RESPONSE

    def test_successful(self):
        post_resp = respx.post(TransactionsBalanceView.ssp_endpoint).mock(
            return_value=httpx.Response(200, json=self.test_response)
        )

        response = self.client.post(
            self.url, self.test_payload, headers=self.api_headers, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post_resp.call_count, 1)

    def test_negative_fail(self):
        test_payload = {
            "balance": {"amount": "-5"},
            "payment_type": "IDEAL",
            "locale": "nl",
        }

        response = self.client.post(
            self.url, test_payload, headers=self.api_headers, format="json"
        )
        self.assertEqual(response.status_code, 400)


class TestTransactionsRechargeConfirmView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-balance-confirm")

        self.test_payload = {
            "order_id": "SSP08",
            "status": "COMPLETED",
            "signature": "123supersignature456",
        }
        self.test_response = wallet_transaction_confirm.MOCK_RESPONSE

    def test_successful_user(self):
        post_resp = respx.post(SSPEndpointExternal.RECHARGE_CONFIRM.value).mock(
            return_value=httpx.Response(200, json=self.test_response)
        )

        response = self.client.post(
            self.url, self.test_payload, headers=self.api_headers, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post_resp.call_count, 1)

    def test_successful_visitor(self):
        api_headers = self.api_headers.copy()
        api_headers["SSP-Access-Token"] = self.test_visitor_token

        post_resp = respx.post(SSPEndpointExternal.RECHARGE_CONFIRM_VISITOR.value).mock(
            return_value=httpx.Response(200, json=self.test_response)
        )  # We are mocking a different URL for visitors!

        response = self.client.post(
            self.url, self.test_payload, headers=api_headers, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post_resp.call_count, 1)


class TestTransactionsListView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-transactions")

        self.test_payload = {
            "page": 1,
            "row_per_page": 10,
            "sort": "paid_at:desc",
            "filters[status]": "COMPLETED",
        }
        self.test_response = transactions.MOCK_RESPONSE

    def test_successful_without_params(self):
        resp = respx.get(TransactionsListView.ssp_endpoint).mock(
            return_value=httpx.Response(200, json=self.test_response)
        )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)

    def test_successful_with_params(self):
        resp = respx.get(TransactionsListView.ssp_endpoint).mock(
            return_value=httpx.Response(200, json=self.test_response)
        )

        response = self.client.get(
            self.url, self.test_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
