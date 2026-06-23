import httpx
import respx
from django.conf import settings
from django.urls import reverse

from bridge.boat_charging.tests.mock_data import init_session
from bridge.boat_charging.tests.views.base_view import BoatChargingTestCase


class TestSessionInitView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-session-init")

    def test_init_session_success(self):
        resp = respx.post(settings.BOAT_CHARGING_ENDPOINTS["SESSIONS"]).mock(
            return_value=httpx.Response(200, json=init_session.MOCK_RESPONSE)
        )

        body = {
            "station_id": "VCPS-IFZTY",
            "socket_number": "1",
            "name": "Test User",
            "email": "user@example.com",
            "return_url": "https://yourdomain.com/app/sessions",
        }
        response = self.client.post(self.url, data=body, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
        self.assertIsNotNone(response.data["checkout_url"])


class TestSessionStartView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.session_id = "foobar"
        self.url = reverse(
            "boat-charging-session-start",
            kwargs={"session_id": self.session_id},
        )

    def test_start_session_success(self):
        url = f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/{self.session_id}/start"
        resp = respx.post(url).mock(return_value=httpx.Response(200, json={}))

        response = self.client.post(self.url, data={}, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)


class TestSessionStopView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.session_id = "foobar"
        self.url = reverse(
            "boat-charging-session-stop",
            kwargs={"session_id": self.session_id},
        )

    def test_stop_session_success(self):
        url = f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/{self.session_id}/stop"
        resp = respx.post(url).mock(return_value=httpx.Response(200, json={}))

        response = self.client.post(self.url, data={}, headers=self.api_headers)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(resp.call_count, 1)
