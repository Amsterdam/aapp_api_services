import httpx
import respx
from django.conf import settings
from django.urls import reverse

from bridge.boat_charging.tests.mock_data import (
    cost_breakdown,
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
        self.assertEqual(len(response.json()["result"]), len(sessions.MOCK_RESPONSE))
        self.assertEqual(
            [item["id"] for item in response.json()["result"]],
            [item["session"]["uniqueId"] for item in sessions.MOCK_RESPONSE],
        )
        self.assertEqual(
            response.json()["page"]["totalElements"], len(sessions.MOCK_RESPONSE)
        )
        self.assertEqual(response.json()["result"][0]["email"], "test@amsterdam.nl")

        for item in response.json()["result"]:
            if item["nrg_status"] == 5:
                self.assertEqual(item["stop_reason"], "cancelled")

        for item in response.json()["result"]:
            if item["nrg_status"] == 2:
                self.assertEqual(
                    item["last_command_error"],
                    "The charge point rejected the start command. Check that the cable is plugged in and try again.",
                )

    def test_pagination_respects_page_and_page_size(self):
        respx.get(settings.BOAT_CHARGING_ENDPOINTS["SESSIONS"]).mock(
            return_value=httpx.Response(200, json=sessions.MOCK_RESPONSE)
        )

        response = self.client.get(
            self.url,
            {"page": 2, "page_size": 1},
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body["result"]), 1)
        self.assertEqual(
            body["result"][0]["id"],
            sessions.MOCK_RESPONSE[1]["session"]["uniqueId"],
        )
        self.assertEqual(body["page"]["number"], 2)
        self.assertEqual(body["page"]["size"], 1)
        self.assertEqual(body["page"]["totalElements"], len(sessions.MOCK_RESPONSE))
        self.assertEqual(body["page"]["totalPages"], len(sessions.MOCK_RESPONSE))
        self.assertIn("self", body["_links"])
        self.assertIn("next", body["_links"])
        self.assertIn("previous", body["_links"])

    def test_status_active_filters_sessions_before_pagination(self):
        respx.get(settings.BOAT_CHARGING_ENDPOINTS["SESSIONS"]).mock(
            return_value=httpx.Response(200, json=sessions.MOCK_RESPONSE)
        )

        response = self.client.get(
            self.url,
            {"status": "ACTIVE", "page": 1, "page_size": 1},
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(
            [item["id"] for item in body["result"]],
            [sessions.ACTIVE_SESSION_IDS[0]],
        )
        self.assertEqual(body["page"]["number"], 1)
        self.assertEqual(body["page"]["size"], 1)
        self.assertEqual(
            body["page"]["totalElements"], len(sessions.ACTIVE_SESSION_IDS)
        )
        self.assertEqual(body["page"]["totalPages"], len(sessions.ACTIVE_SESSION_IDS))
        self.assertIn("status=ACTIVE", body["_links"]["self"]["href"])
        self.assertIn("status=ACTIVE", body["_links"]["next"]["href"])

    def test_status_completed_filters_sessions(self):
        respx.get(settings.BOAT_CHARGING_ENDPOINTS["SESSIONS"]).mock(
            return_value=httpx.Response(200, json=sessions.MOCK_RESPONSE)
        )

        response = self.client.get(
            self.url,
            {"status": "COMPLETED"},
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(
            [item["id"] for item in body["result"]],
            [sessions.COMPLETED_SESSION_ID],
        )
        self.assertEqual(body["page"]["totalElements"], 1)
        self.assertEqual(body["page"]["totalPages"], 1)

    def test_response_no_sessions(self):
        respx.get(settings.BOAT_CHARGING_ENDPOINTS["SESSIONS"]).mock(
            return_value=httpx.Response(200, json=[])
        )

        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["result"]), 0)
        self.assertEqual(response.json()["page"]["totalElements"], 0)


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
            f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/"
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

    def test_unknown_statuses_are_rejected(self):
        respx.get(self.external_endpoint).mock(
            return_value=httpx.Response(
                200,
                json=socket_status.MOCK_RESPONSE_UNKNOWN_STATUS,
            )
        )

        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 400)

    def test_invalid_session_id_returns_400(self):
        invalid_url = reverse(
            "boat-charging-session-socket-status",
            kwargs={"session_id": "invalid$id"},
        )

        response = self.client.get(invalid_url, headers=self.api_headers)

        self.assertEqual(response.status_code, 400)


class TestSessionCostBreakdownView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.session_id = "foobar"
        self.url = reverse(
            "boat-charging-session-cost-breakdown",
            kwargs={"session_id": self.session_id},
        )
        self.external_endpoint = (
            f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/"
            f"{self.session_id}/cost-breakdown"
        )

    def test_success(self):
        respx.get(self.external_endpoint).mock(
            return_value=httpx.Response(
                200,
                json=cost_breakdown.MOCK_RESPONSE,
            )
        )

        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["total_incl_vat"],
            cost_breakdown.MOCK_RESPONSE["totalInclVat"],
        )
        self.assertEqual(len(response.json()["items"]), 3)

    def test_invalid_session_id_returns_400(self):
        invalid_url = reverse(
            "boat-charging-session-cost-breakdown",
            kwargs={"session_id": "invalid$id"},
        )

        response = self.client.get(invalid_url, headers=self.api_headers)

        self.assertEqual(response.status_code, 400)

    def test_404_response_to_400(self):
        respx.get(self.external_endpoint).mock(
            return_value=httpx.Response(
                404,
                json={"detail": "Session not found"},
            )
        )

        response = self.client.get(self.url, headers=self.api_headers)

        self.assertContains(response, "Session not found", status_code=400)
