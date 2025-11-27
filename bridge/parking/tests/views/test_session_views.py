import json
from datetime import datetime, timezone

import responses
from django.urls import reverse
from freezegun import freeze_time
from uritemplate import URITemplate

from bridge.parking.services.ssp import SSPEndpointExternal
from bridge.parking.tests.mock_data_external import (
    cost_calculator,
    parking_session_activate,
    parking_session_edit,
    parking_session_list,
    parking_session_start,
)
from bridge.parking.tests.views.test_base_ssp_view import BaseSSPTestCase
from bridge.parking.views.session_views import (
    ParkingSessionActivateView,
    ParkingSessionListView,
    ParkingSessionReceiptView,
    ParkingSessionVisitorListView,
)


class TestParkingSessionActivateView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-session-activate")
        self.payload = {"report_code": "1001", "vehicle_id": "SSP123"}
        self.test_response = parking_session_activate.MOCK_RESPONSE

    def test_successful(self):
        resp = responses.post(
            ParkingSessionActivateView.ssp_endpoint, json=self.test_response
        )

        response = self.client.post(
            self.url, data=self.payload, format="json", headers=self.api_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)


class TestParkingSessionListView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-sessions")
        self.payload = {
            "page": 1,
            "row_per_page": 10,
            "sort": "parking_session_id:desc",
        }
        self.test_response = parking_session_list.MOCK_RESPONSE

    def test_successful(self):
        resp = responses.post(
            ParkingSessionListView.ssp_endpoint, json=self.test_response
        )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)

    def test_successful_with_params(self):
        resp = responses.post(
            ParkingSessionListView.ssp_endpoint, json=self.test_response
        )

        response = self.client.get(self.url, self.payload, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)


class TestParkingSessionVisitorListView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-visitor-sessions")
        self.payload = {
            "page": 1,
            "row_per_page": 10,
            "sort": "parking_session_id:desc",
        }
        self.test_response = parking_session_list.MOCK_RESPONSE

    def test_successful(self):
        resp = responses.post(
            ParkingSessionVisitorListView.ssp_endpoint, json=self.test_response
        )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)

    def test_successful_with_params(self):
        resp = responses.post(
            ParkingSessionVisitorListView.ssp_endpoint, json=self.test_response
        )

        response = self.client.get(self.url, self.payload, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)


class TestParkingSessionStartUpdateDeleteView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-session-start-update-delete")
        self.start_payload = {
            "parking_session": {
                "vehicle_id": "AB124C",
                "start_date_time": datetime.now().isoformat(),
                "end_date_time": datetime.now().isoformat(),
                "report_code": "1004",
                "payment_zone_id": "100000000",
            }
        }
        self.patch_payload = {
            "ps_right_id": "10000",
            "end_date_time": datetime.now().isoformat(),
        }
        self.start_response_user = parking_session_start.MOCK_RESPONSE_USER
        self.start_response_visitor = parking_session_start.MOCK_RESPONSE_VISITOR
        self.patch_response = parking_session_edit.MOCK_RESPONSE
        self.api_headers = {**self.api_headers, "DeviceId": "test-device-id"}
        self.test_visitor_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjEwMzkxNTYsImV4cCI6MTc2MTA0Mjc1Niwicm9sZXMiOlsiUk9MRV9WSVNJVE9SX1NTUCJdLCJsb2dpbl9tZXRob2QiOiJsb2dpbl9mb3JtX3NzcCIsInVzZXJuYW1lIjoiYmxhIiwibG9jYWxlIjoibmwtTkwiLCJjbGllbnRfcHJvZHVjdF9pZCI6MTB9.jQNCTjqM0c9AgRPp-kgmvjjmrU-D2kwlcBSBBAgShPg%AMSTERDAMAPP%eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjEwMzkxNTYsImV4cCI6MTc2MTA0Mjc1Niwicm9sZXMiOlsiUk9MRV9WSVNJVE9SX1NTUCJdLCJsb2dpbl9tZXRob2QiOiJsb2dpbl9mb3JtX3NzcCIsInVzZXJuYW1lIjoiYmxhIiwibG9jYWxlIjoibmwtTkwiLCJjbGllbnRfcHJvZHVjdF9pZCI6MTB9.jQNCTjqM0c9AgRPp-kgmvjjmrU-D2kwlcBSBBAgShPg"
        self.test_no_role_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjEwMzkxNTYsImV4cCI6MTc2MTA0Mjc1NiwibG9naW5fbWV0aG9kIjoibG9naW5fZm9ybV9zc3AiLCJ1c2VybmFtZSI6ImJsYSIsImxvY2FsZSI6Im5sLU5MIiwiY2xpZW50X3Byb2R1Y3RfaWQiOjEwfQ.ESkkJTBjC6avkLsfibvdTExa8mrGLKDiYxR9JVt6RS4%AMSTERDAMAPP%eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjEwMzkxNTYsImV4cCI6MTc2MTA0Mjc1NiwibG9naW5fbWV0aG9kIjoibG9naW5fZm9ybV9zc3AiLCJ1c2VybmFtZSI6ImJsYSIsImxvY2FsZSI6Im5sLU5MIiwiY2xpZW50X3Byb2R1Y3RfaWQiOjEwfQ.ESkkJTBjC6avkLsfibvdTExa8mrGLKDiYxR9JVt6RS4"

    def test_successful_start_user(self):
        self.start_session(
            payload=self.start_payload,
            api_headers=self.api_headers,
            status_code=200,
            resp_count=1,
        )

    def test_successful_start_parking_machine(self):
        payload = self.start_payload.copy()
        payload["parking_session"]["parking_machine"] = "12345"
        payload["parking_session"].pop("payment_zone_id")
        self.start_session(
            payload=payload, api_headers=self.api_headers, status_code=200, resp_count=1
        )

    def test_fail_start_both_zone_and_machine(self):
        payload = self.start_payload.copy()
        payload["parking_session"]["parking_machine"] = "12345"
        self.start_session(
            payload=payload, api_headers=self.api_headers, status_code=400, resp_count=0
        )

    def test_successful_start_visitor(self):
        api_headers = self.api_headers.copy()
        api_headers["SSP-Access-Token"] = self.test_visitor_token
        payload = self.start_payload.copy()
        self.start_session(
            payload=payload,
            api_headers=api_headers,
            status_code=200,
            resp_count=1,
            is_visitor=True,
        )

    def test_error_start_no_role(self):
        api_headers = self.api_headers.copy()
        api_headers["SSP-Access-Token"] = self.test_no_role_token
        payload = self.start_payload.copy()
        self.start_session(
            payload=payload, api_headers=api_headers, status_code=401, resp_count=0
        )

    def start_session(
        self, payload, api_headers, status_code, resp_count, is_visitor=False
    ):
        if is_visitor:
            resp = responses.post(
                SSPEndpointExternal.PARKING_SESSION_START.value,
                json=self.start_response_visitor,
            )
        else:
            resp = responses.post(
                SSPEndpointExternal.PARKING_SESSION_START.value,
                json=self.start_response_user,
            )
        response = self.client.post(
            self.url, data=payload, format="json", headers=api_headers
        )
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(resp.call_count, resp_count)
        if status_code == 200:
            received_payload = resp.calls[0].request.body
            received_payload = json.loads(received_payload)["data"]
            expected_started_at = datetime.fromisoformat(
                payload["parking_session"]["start_date_time"]
            )
            self.assertLess(
                datetime.fromisoformat(received_payload["started_at"].split("+")[0]),
                expected_started_at,
            )
            expected_started_utc = expected_started_at.astimezone(timezone.utc)
            self.assertEqual(
                datetime.fromisoformat(received_payload["started_at"]),
                expected_started_utc,
            )

    @freeze_time("2025-07-24T11:30:00.000Z")
    def test_exception_start_time_in_past_within_limits(self):
        payload = self.start_payload.copy()
        payload["start_date_time"] = "2025-07-24T11:29:00.000Z"
        self.start_session(
            payload=self.start_payload,
            api_headers=self.api_headers,
            status_code=200,
            resp_count=1,
        )

    @freeze_time("2025-07-24T11:30:00.000Z")
    def test_exception_start_time_in_past_outside_limits(self):
        payload = self.start_payload.copy()
        payload["start_date_time"] = "2025-07-24T11:05:00.000Z"
        self.start_session(
            payload=self.start_payload,
            api_headers=self.api_headers,
            status_code=200,
            resp_count=1,
        )

    def test_successful_patch(self):
        url_template = SSPEndpointExternal.PARKING_SESSION_EDIT.value
        url = URITemplate(url_template).expand(session_id=10000)
        resp = responses.patch(url, json=self.patch_response)

        response = self.client.patch(
            self.url,
            data={"parking_session": self.patch_payload},
            format="json",
            headers=self.api_headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)

    def test_successful_delete(self):
        url_template = SSPEndpointExternal.PARKING_SESSION_EDIT.value
        url = URITemplate(url_template).expand(session_id=10000)
        resp = responses.patch(url, json=self.patch_response)

        response = self.client.delete(
            self.url, query_params=self.patch_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)


class TestParkingSessionReceiptView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-session-receipt")
        self.payload = {
            "report_code": 10001,
            "start_date_time": datetime.now().isoformat(),
            "end_date_time": datetime.now().isoformat(),
        }
        self.mock_response = cost_calculator.MOCK_RESPONSE

    def test_successful_payment_zone(self):
        resp = responses.post(
            ParkingSessionReceiptView.ssp_endpoint, json=self.mock_response
        )
        payload = self.payload.copy()
        payload["payment_zone_id"] = 37

        response = self.client.get(
            self.url, query_params=payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)

    def test_successful_parking_machine(self):
        resp = responses.post(
            ParkingSessionReceiptView.ssp_endpoint, json=self.mock_response
        )
        payload = self.payload.copy()
        payload["parking_machine"] = 1037

        response = self.client.get(
            self.url, query_params=payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)

    def test_exception_both(self):
        responses.post(ParkingSessionReceiptView.ssp_endpoint, json=self.mock_response)
        payload = self.payload.copy()
        payload["payment_zone_id"] = 37
        payload["parking_machine"] = 1037

        response = self.client.get(
            self.url, query_params=payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 400)
