import httpx
import respx
from django.conf import settings
from django.urls import reverse

from bridge.boat_charging.tests.mock_data import (
    session_detail,
    sessions,
    socket_status,
)
from bridge.boat_charging.tests.views.base_view import BoatChargingTestCase
from bridge.boat_charging.views.session_view import SessionView


class TestSessionView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-sessions")
        self.view = SessionView()

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
        self.external_endpoint = (
            f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/{self.session_id}"
        )

    def test_success(self):
        resp = respx.get(self.external_endpoint).mock(
            return_value=httpx.Response(200, json=session_detail.MOCK_RESPONSE_CHARGING)
        )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)

    def test_invalid_session_id_returns_400(self):
        invalid_url = reverse(
            "boat-charging-session-detail",
            kwargs={"session_id": "invalid$id"},
        )
        response = self.client.get(invalid_url, headers=self.api_headers)

        self.assertEqual(response.status_code, 400)


class TestSessionSocketStatusView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.session_id = "foobar"
        self.url = reverse(
            "boat-charging-session-socket-status",
            kwargs={"session_id": self.session_id},
        )
        self.external_endpoint = (
            f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS_SOCKET_STATUS']}/"
            f"{self.session_id}/socket-status"
        )

    def test_success(self):
        resp = respx.get(self.external_endpoint).mock(
            return_value=httpx.Response(
                200,
                json=socket_status.MOCK_RESPONSE_OCCUPIED_PREPARING,
            )
        )

        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(), socket_status.MOCK_RESPONSE_OCCUPIED_PREPARING
        )
        self.assertEqual(resp.call_count, 1)

    def test_unknown_statuses_are_forwarded_without_changes(self):
        respx.get(self.external_endpoint).mock(
            return_value=httpx.Response(
                200,
                json=socket_status.MOCK_RESPONSE_UNKNOWN_STATUS,
            )
        )

        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), socket_status.MOCK_RESPONSE_UNKNOWN_STATUS)

    def test_invalid_session_id_returns_400(self):
        invalid_url = reverse(
            "boat-charging-session-socket-status",
            kwargs={"session_id": "invalid$id"},
        )

        response = self.client.get(invalid_url, headers=self.api_headers)

        self.assertEqual(response.status_code, 400)
