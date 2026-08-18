from unittest.mock import AsyncMock, patch

import httpx
import respx
from django.conf import settings
from django.urls import reverse
from model_bakery import baker

from bridge.boat_charging.tests.mock_data import init_session, session_start
from bridge.boat_charging.tests.views.base_view import BoatChargingTestCase
from notification.models import BoatChargingSession


class TestSessionInitView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-session-init")

    def _get_request_body(self, return_url="https://yourdomain.com/app/sessions"):
        return {
            "station_id": "VCPS-IFZTY",
            "socket_number": "1",
            "name": "Test User",
            "email": "user@example.com",
            "return_url": return_url,
        }

    def test_init_session_success(self):
        resp = respx.post(settings.BOAT_CHARGING_ENDPOINTS["SESSIONS"]).mock(
            return_value=httpx.Response(200, json=init_session.MOCK_RESPONSE)
        )

        body = self._get_request_body()
        response = self.client.post(self.url, data=body, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
        self.assertIsNotNone(response.data["checkout_url"])

    def test_init_session_accepts_deeplink_return_url(self):
        resp = respx.post(settings.BOAT_CHARGING_ENDPOINTS["SESSIONS"]).mock(
            return_value=httpx.Response(200, json=init_session.MOCK_RESPONSE)
        )

        body = self._get_request_body(return_url="amsterdam://some-module/some-action")
        response = self.client.post(self.url, data=body, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
        self.assertIsNotNone(response.data["checkout_url"])

    def test_init_no_token_success(self):
        self.api_headers.pop("access_token")
        self.test_init_session_success()


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
        resp = respx.post(url).mock(
            return_value=httpx.Response(200, json=session_start.MOCK_RESPONSE)
        )

        response = self.client.post(self.url, data={}, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
        self.assertEqual(BoatChargingSession.objects.count(), 1)

    @patch(
        "bridge.boat_charging.views.base_view.client.request", new_callable=AsyncMock
    )
    def test_start_session_uses_extended_timeout(self, mocked_request):
        mocked_request.return_value = httpx.Response(
            200, json=session_start.MOCK_RESPONSE
        )

        response = self.client.post(self.url, data={}, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        timeout = mocked_request.await_args.kwargs["timeout"]
        self.assertEqual(timeout.read, 180.0)

    def test_missing_device_id(self):
        self.api_headers.pop("DeviceId")
        response = self.client.post(self.url, data={}, headers=self.api_headers)

        self.assertEqual(response.status_code, 400)


class TestSessionStopView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.session_id = "foobar"
        self.url = reverse(
            "boat-charging-session-stop",
            kwargs={"session_id": self.session_id},
        )

    def test_stop_session_success(self):
        baker.make(
            BoatChargingSession,
            device__external_id=self.api_headers["DeviceId"],
            session_id=self.session_id,
        )

        url = f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/{self.session_id}/stop"
        resp = respx.post(url).mock(return_value=httpx.Response(200, json={}))

        response = self.client.post(self.url, data={}, headers=self.api_headers)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(resp.call_count, 1)
        self.assertTrue(
            BoatChargingSession.objects.filter(session_id=self.session_id)
            .first()
            .deleted
        )

    @patch(
        "bridge.boat_charging.views.base_view.client.request", new_callable=AsyncMock
    )
    def test_stop_session_keeps_default_timeout(self, mocked_request):
        mocked_request.return_value = httpx.Response(200, json={})
        baker.make(
            BoatChargingSession,
            device__external_id=self.api_headers["DeviceId"],
            session_id=self.session_id,
        )

        response = self.client.post(self.url, data={}, headers=self.api_headers)

        self.assertEqual(response.status_code, 204)
        self.assertNotIn("timeout", mocked_request.await_args.kwargs)

    def test_missing_device_id(self):
        self.api_headers.pop("DeviceId")
        response = self.client.post(self.url, data={}, headers=self.api_headers)

        self.assertEqual(response.status_code, 400)


class TestSessionCancelView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.session_id = "foobar"
        self.url = reverse(
            "boat-charging-session-cancel",
            kwargs={"session_id": self.session_id},
        )

    def test_cancel_session_success(self):
        baker.make(
            BoatChargingSession,
            device__external_id=self.api_headers["DeviceId"],
            session_id=self.session_id,
        )

        url = f"{settings.BOAT_CHARGING_ENDPOINTS['SESSIONS']}/{self.session_id}/cancel"
        resp = respx.post(url).mock(return_value=httpx.Response(200, json={}))

        response = self.client.post(self.url, data={}, headers=self.api_headers)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(resp.call_count, 1)
        self.assertTrue(
            BoatChargingSession.objects.filter(session_id=self.session_id)
            .first()
            .deleted
        )

    def test_missing_device_id(self):
        self.api_headers.pop("DeviceId")
        response = self.client.post(self.url, data={}, headers=self.api_headers)

        self.assertEqual(response.status_code, 400)
