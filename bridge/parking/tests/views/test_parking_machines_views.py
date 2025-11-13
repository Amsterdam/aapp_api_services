import responses
from django.urls import reverse

from bridge.parking.services.ssp import SSPEndpointExternal
from bridge.parking.tests.mock_data import parking_machines
from bridge.parking.tests.views.test_base_ssp_view import BaseSSPTestCase


class TestParkingVisitorTimeBalanceView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-machines-list")
        self.rsp_get = responses.get(
            SSPEndpointExternal.PARKING_MACHINES_LIST.value,
            body=parking_machines.MOCK_RESPONSE,
            headers={"Content-Type": "text/plain"},
        )

    def test_success(self):
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.json()), 43
        )  # Only Amsterdam machines are returned. Data contains 3 other machines

    def test_cache(self):
        self.assert_caching(self.url, rsp_get=self.rsp_get)
