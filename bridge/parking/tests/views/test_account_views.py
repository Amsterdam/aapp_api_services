import freezegun
import responses
from django.conf import settings
from django.urls import reverse

from bridge.parking.exceptions import SSPResponseError
from bridge.parking.services.ssp import SSPEndpoint, SSPEndpointExternal
from bridge.parking.tests.mock_data import permit, permits
from bridge.parking.tests.views.test_base_ssp_view import BaseSSPTestCase


class TestParkingAccountLoginView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-account-login")
        self.test_payload = {"report_code": "10000000", "pin": "1234"}

        self.test_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3NTY4MTYxOTQsImV4cCI6MTc1NjgxOTc5NCwicm9sZXMiOlsiUk9MRV9VU0VSX1NTUCJdLCJsb2dpbl9tZXRob2QiOiJsb2dpbl9mb3JtX3NzcCIsInVzZXJuYW1lIjoiZmlwczp0RmswZlJMUDA3WERLUll4YXU3TTJ6MUJ2djZGZmlLYUpsSjlLaDUtaW1nTlAtRWlEVHBVeW9JYXp0Vkc3YkNxdks2X1VhQWkxN2NhZjF1d3Z6NmFsQXBIZ2xobzVQdlJvWHpadDlFVlF6MjhTZ1U3c3F0TnU4WmR2QlFORUR2MHEwV0Z2OF9leG9FPSIsImxvY2FsZSI6Im5sLU5MIn0.HatOyxHBqFjYXRb1DfaPWVZGwN3RQ3R_BTZEmKqge6eonxaDLgBCBMTUwaKppj7DtnLII4-DkIzKxj-LeP0sfMkqlpFoQKJTMPX2bidZr0_FwlQ7Dm1Mxd284EQqx132HK0Xke4jjqXxE7elR7iZYDjnDoYnXl85PkjEBMcYsSHRj0ibWvH1ChkGyXpEgfwCy4uqQYRM7iOF3-A6dvgV5ti9kSkcxP5IK_7Z7SRDuhbxMEdL_ON3eJdErs7HraxGowL_HlncKnwSZO82KHObUKpZeLvdSA4CHAiCmnyFlunCMOsH5hWM99ys00rEEMvha3AsXFhLTm5uRmmoA2nwvCR5BR4tu3olhm0NG9PAuWny2rmbCrFtz739-WOX1lzP6Xxuo6cC4lU_gy2AkI3QYtQ2Hj-rRQ-3peZcBpQ49nS-VNCnrMjLo6S2BW4I6SYamN3-0mhqFSnyUZ9YiQbwaLhmJJqXzou-kFuvtY6OX_afm5deh8CfFUO03O6C0bVJ-8oSC61QAEIEdNaJR0Vb2dqAM9qAJWPP-SNr_dqte9eCV05POf0XT0ZkjtHmrM678fzIjE-tGJSN-LrumrYXZU8zVTqNBw57sDhuUROhQLDSeqoLbKJHkoQYSFIMWlouhanAegSuHFzZRmb8SkHhZ0bLyUZkFM9Rvozy21M2YKU"
        self.test_response = {
            "token": self.test_token,
        }
        self.test_response_no_role = {
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjEwMzkxNTYsImV4cCI6MTc2MTA0Mjc1Niwicm9sZXMiOlsiT1RIRVJfUk9MRSJdLCJsb2dpbl9tZXRob2QiOiJsb2dpbl9mb3JtX3NzcCIsInVzZXJuYW1lIjoiYmxhIiwibG9jYWxlIjoibmwtTkwiLCJjbGllbnRfcHJvZHVjdF9pZCI6MTB9.KRVI2yW-RpPhPeGmhAw3FnQ_nqQOHO2-rErWH4bE2pc"
        }

    @freezegun.freeze_time("2024-09-02T15:30:00")
    def test_successful_login(self):
        post_resp = responses.post(SSPEndpoint.LOGIN.value, json=self.test_response)
        post_resp_ext = responses.post(
            SSPEndpointExternal.LOGIN.value, json=self.test_response
        )

        response = self.client.post(
            self.url, self.test_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post_resp.call_count, 1)
        self.assertEqual(post_resp_ext.call_count, 1)
        self.assertEqual(
            response.data["access_token"],
            self.test_token + "%AMSTERDAMAPP%" + self.test_token,
        )
        self.assertEqual(response.data["scope"], "permitHolder")
        expiration_datetime = "2024-09-02T15:45:00+02:00"
        self.assertEqual(
            response.data["access_token_expiration"],
            expiration_datetime,
        )

    def test_missing_ssp_response_values(self):
        post_resp = responses.post(SSPEndpoint.LOGIN.value, json={"not_token": "value"})

        response = self.client.post(
            self.url, self.test_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(post_resp.call_count, 1)
        self.assertEqual(response.data["code"], SSPResponseError.default_code)

    def test_unknown_role(self):
        post_resp = responses.post(
            SSPEndpoint.LOGIN.value, json=self.test_response_no_role
        )
        post_resp_ext = responses.post(
            SSPEndpointExternal.LOGIN.value, json=self.test_response
        )

        response = self.client.post(
            self.url, self.test_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(post_resp.call_count, 1)
        self.assertEqual(post_resp_ext.call_count, 1)

    def test_no_ssp_token(self):
        post_resp = responses.post(SSPEndpoint.LOGIN.value, json={"not_token": "value"})

        del self.api_headers[settings.SSP_ACCESS_TOKEN_HEADER]

        response = self.client.post(
            self.url, self.test_payload, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(post_resp.call_count, 1)
        self.assertEqual(response.data["code"], SSPResponseError.default_code)

    def test_ssp_login_failed(self):
        ssp_login_failed_messages = [
            "The presented password is invalid.",
            "Bad credentials.",
        ]

        for message in ssp_login_failed_messages:
            json_response = {"code": 401, "message": message}
            responses.post(SSPEndpoint.LOGIN.value, status=401, json=json_response)
            responses.post(
                SSPEndpointExternal.LOGIN.value, status=401, json=json_response
            )
            response = self.client.post(
                self.url, self.test_payload, headers=self.api_headers
            )
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.data["code"], "SSP_BAD_CREDENTIALS")


class TestParkingAccountDetailsView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-account-details")
        self.mock_permits_response = permits.MOCK_RESPONSE
        self.mock_permit_detail_response = permit.MOCK_RESPONSE_VISITOR_HOLDER
        self.test_permitholder_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjEwMzkxNTYsImV4cCI6MTc2MTA0Mjc1Niwicm9sZXMiOlsiUk9MRV9VU0VSX1NTUCJdLCJsb2dpbl9tZXRob2QiOiJsb2dpbl9mb3JtX3NzcCIsInVzZXJuYW1lIjoiYmxhIiwibG9jYWxlIjoibmwtTkwiLCJjbGllbnRfcHJvZHVjdF9pZCI6MTB9.sRkWR4ZM3WFvg4B17QUStrWvkhsDH7xK7QfScGYt6yw%AMSTERDAMAPP%eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjEwMzkxNTYsImV4cCI6MTc2MTA0Mjc1Niwicm9sZXMiOlsiUk9MRV9VU0VSX1NTUCJdLCJsb2dpbl9tZXRob2QiOiJsb2dpbl9mb3JtX3NzcCIsInVzZXJuYW1lIjoiYmxhIiwibG9jYWxlIjoibmwtTkwiLCJjbGllbnRfcHJvZHVjdF9pZCI6MTB9.sRkWR4ZM3WFvg4B17QUStrWvkhsDH7xK7QfScGYt6yw"

    def test_success_permitholder(self):
        api_headers = self.api_headers.copy()
        api_headers["SSP-Access-Token"] = f"{self.test_permitholder_token}"

        resp_list = responses.get(
            SSPEndpoint.PERMITS.value, json=self.mock_permits_response
        )
        permit_detail_template = SSPEndpoint.PERMIT.value
        # Only mock the permit 10001 because it is a visitor permit
        permit_detail_url = permit_detail_template.format(permit_id=10001)
        resp_detail = responses.get(
            permit_detail_url, json=self.mock_permit_detail_response
        )

        response = self.client.get(self.url, headers=api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp_list.call_count, 1)
        self.assertEqual(resp_detail.call_count, 1)

    def test_success_visitor(self):
        api_headers = self.api_headers.copy()
        api_headers["SSP-Access-Token"] = self.test_visitor_token

        response = self.client.get(self.url, headers=api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["wallet"]["balance"], 0)

    def test_success_permitholder_no_permits(self):
        api_headers = self.api_headers.copy()
        api_headers["SSP-Access-Token"] = f"{self.test_permitholder_token}"
        resp_list = responses.get(SSPEndpoint.PERMITS.value, json={"data": []})

        response = self.client.get(self.url, headers=api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["wallet"]["balance"], None)
        self.assertEqual(resp_list.call_count, 1)
