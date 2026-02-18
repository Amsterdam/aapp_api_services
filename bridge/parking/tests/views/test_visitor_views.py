import json

import httpx
import respx
from django.urls import reverse
from uritemplate import URITemplate

from bridge.parking.services.ssp import SSPEndpoint
from bridge.parking.tests.mock_data import (
    visitor_activate,
    visitor_allocate,
    visitor_deactivate,
    visitor_withdraw,
)
from bridge.parking.tests.views.base_ssp_view import BaseSSPTestCase


class TestParkingVisitorTimeBalanceView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-visitor-time-balance")
        self.permit_id = 1004
        self.url = reverse("parking-visitor-time-balance")

    def test_successful_add(self):
        url_template = SSPEndpoint.VISITOR_ALLOCATE.value
        url = URITemplate(url_template).expand(permit_id=self.permit_id)
        resp = respx.post(url).mock(
            return_value=httpx.Response(200, json=visitor_allocate.MOCK_RESPONSE)
        )

        payload = {"seconds_to_transfer": 3600, "report_code": self.permit_id}
        response = self.client.post(self.url, payload, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)

    def test_successful_withdraw(self):
        url_template = SSPEndpoint.VISITOR_DEALLOCATE.value
        url = URITemplate(url_template).expand(permit_id=self.permit_id)
        resp = respx.post(url).mock(
            return_value=httpx.Response(200, json=visitor_withdraw.MOCK_RESPONSE)
        )

        payload = {"seconds_to_transfer": -3600, "report_code": self.permit_id}
        response = self.client.post(self.url, payload, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)

    def test_0_raises_error(self):
        payload = {"seconds_to_transfer": 0, "report_code": self.permit_id}
        response = self.client.post(self.url, payload, headers=self.api_headers)
        self.assertEqual(response.status_code, 400)

    def test_rounds_down_to_nearest_hour(self):
        url_template = SSPEndpoint.VISITOR_ALLOCATE.value
        url = URITemplate(url_template).expand(permit_id=self.permit_id)
        resp = respx.post(url).mock(
            return_value=httpx.Response(200, json=visitor_allocate.MOCK_RESPONSE)
        )

        payload = {"seconds_to_transfer": 4500, "report_code": self.permit_id}
        response = self.client.post(self.url, payload, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
        self.assertEqual(json.loads(resp.calls[0].request.content), {"amount": 1})

    def test_rounds_up_to_nearest_hour(self):
        url_template = SSPEndpoint.VISITOR_ALLOCATE.value
        url = URITemplate(url_template).expand(permit_id=self.permit_id)
        resp = respx.post(url).mock(
            return_value=httpx.Response(200, json=visitor_allocate.MOCK_RESPONSE)
        )

        payload = {"seconds_to_transfer": 5500, "report_code": self.permit_id}
        response = self.client.post(self.url, payload, headers=self.api_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
        self.assertEqual(json.loads(resp.calls[0].request.content), {"amount": 2})


class TestParkingVisitorView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.permit_id = 1004
        self.url = reverse("parking-visitor-post-delete", args=[self.permit_id])
        self.test_visitor_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjEwMzkxNTYsImV4cCI6MTc2MTA0Mjc1Niwicm9sZXMiOlsiUk9MRV9WSVNJVE9SX1NTUCJdLCJsb2dpbl9tZXRob2QiOiJsb2dpbl9mb3JtX3NzcCIsInVzZXJuYW1lIjoiYmxhIiwibG9jYWxlIjoibmwtTkwiLCJjbGllbnRfcHJvZHVjdF9pZCI6MTB9.jQNCTjqM0c9AgRPp-kgmvjjmrU-D2kwlcBSBBAgShPg%AMSTERDAMAPP%eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjEwMzkxNTYsImV4cCI6MTc2MTA0Mjc1Niwicm9sZXMiOlsiUk9MRV9WSVNJVE9SX1NTUCJdLCJsb2dpbl9tZXRob2QiOiJsb2dpbl9mb3JtX3NzcCIsInVzZXJuYW1lIjoiYmxhIiwibG9jYWxlIjoibmwtTkwiLCJjbGllbnRfcHJvZHVjdF9pZCI6MTB9.jQNCTjqM0c9AgRPp-kgmvjjmrU-D2kwlcBSBBAgShPg"

    def test_successful_create(self):
        url_template = SSPEndpoint.VISITOR_CREATE.value
        url = URITemplate(url_template).expand(permit_id=self.permit_id)
        resp = respx.post(url).mock(
            return_value=httpx.Response(200, json=visitor_activate.MOCK_RESPONSE)
        )

        response = self.client.post(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)

    def test_visitor_not_allowed_error(self):
        url_template = SSPEndpoint.VISITOR_CREATE.value
        url = URITemplate(url_template).expand(permit_id=self.permit_id)
        resp = respx.post(url).mock(
            return_value=httpx.Response(200, json=visitor_activate.MOCK_RESPONSE)
        )

        api_headers = self.api_headers.copy()
        api_headers["SSP-Access-Token"] = self.test_visitor_token

        response = self.client.post(self.url, headers=api_headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(resp.call_count, 0)

    def test_successful_delete(self):
        url_template = SSPEndpoint.VISITOR_DELETE.value
        url = URITemplate(url_template).expand(permit_id=self.permit_id)
        resp = respx.post(url).mock(
            return_value=httpx.Response(200, json=visitor_deactivate.MOCK_RESPONSE)
        )

        response = self.client.delete(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
