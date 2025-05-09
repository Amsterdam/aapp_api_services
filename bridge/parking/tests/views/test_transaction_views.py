import re

import responses
from django.urls import reverse

from bridge.parking.serializers.transaction_serializers import (
    TransactionResponseSerializer,
)
from bridge.parking.services.ssp import SSPEndpoint
from bridge.parking.tests.views.test_base_ssp_view import (
    BaseSSPTestCase,
    create_meta_pagination_data,
)
from core.utils.serializer_utils import create_serializer_data


class TestTransactionsListView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-transactions")

    @responses.activate
    def test_get_list_result_successfully(self):
        single_transaction_item_dict = create_serializer_data(
            TransactionResponseSerializer
        )
        transaction_item_list = [single_transaction_item_dict]
        mock_response_content = {
            "data": transaction_item_list,
            "meta": create_meta_pagination_data(),
            "totalActiveParkingSessions": 1,
            "totalUpcomingParkingSessions": 0,
            "totalFinishedParkingSessions": 0,
        }
        responses.get(
            re.compile(SSPEndpoint.TRANSACTIONS.value + ".*"),
            json=mock_response_content,
        )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["result"], transaction_item_list)
