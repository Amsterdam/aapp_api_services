import httpx
import respx
from django.conf import settings
from django.urls import reverse

from bridge.boat_charging.tests.mock_data import (
    session_detail,
    sessions,
)
from bridge.boat_charging.tests.views.base_view import BoatChargingTestCase


class TestSessionView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-sessions")

    def test_success(self):
        resp = respx.get(settings.BOAT_CHARGING_ENDPOINTS["SESSIONS"]).mock(
            return_value=httpx.Response(200, json=sessions.MOCK_RESPONSE)
        )
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)


class TestSessionDetailView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.session_id = "foobar"
        self.url = reverse(
            "boat-charging-session-detail", kwargs={"session_id": self.session_id}
        )

    def test_success(self):

        ext_endpoint = (
            f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/{self.session_id}"
        )
        resp = respx.get(ext_endpoint).mock(
            return_value=httpx.Response(200, json=session_detail.MOCK_RESPONSE)
        )
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
