import anyio
import httpx
import respx
from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from uritemplate import URITemplate

from bridge.parking.services.ssp import SSPEndpoint, SSPEndpointExternal
from bridge.parking.tests.mock_data import (
    paid_parking_zone,
    permit,
    permits,
)
from bridge.parking.tests.mock_data_external import parking_zone_by_machine
from bridge.parking.tests.views.base_ssp_view import BaseSSPTestCase
from bridge.parking.views.permit_views import (
    ParkingPermitsView,
    ParkingPermitZoneByMachineView,
)


class TestParkingPermitsView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-permits")
        self.mock_response = permits.MOCK_RESPONSE

    def test_success(self):
        resp = respx.get(ParkingPermitsView.ssp_endpoint).mock(
            return_value=httpx.Response(200, json=self.mock_response)
        )
        permit_detail_template = SSPEndpoint.PERMIT.value
        parking_zone_template = SSPEndpoint.PAID_PARKING_ZONE.value
        for permit_id in ["1003", "10001", "1001"]:
            permit_detail_url = URITemplate(permit_detail_template).expand(
                permit_id=permit_id
            )
            respx.get(permit_detail_url).mock(
                return_value=httpx.Response(
                    200, json=permit.MOCK_RESPONSE_VISITOR_HOLDER
                )
            )
            parking_zone_url = URITemplate(parking_zone_template).expand(
                permit_id=permit_id
            )
            respx.get(parking_zone_url).mock(
                return_value=httpx.Response(200, json=paid_parking_zone.MOCK_RESPONSE)
            )

        self.api_headers[settings.SSP_ACCESS_TOKEN_HEADER] = (
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3NTY4MTYxOTQsImV4cCI6MTc1NjgxOTc5NCwicm9sZXMiOlsiUk9MRV9VU0VSX1NTUCJdLCJsb2dpbl9tZXRob2QiOiJsb2dpbl9mb3JtX3NzcCIsInVzZXJuYW1lIjoiZmlwczp0RmswZlJMUDA3WERLUll4YXU3TTJ6MUJ2djZGZmlLYUpsSjlLaDUtaW1nTlAtRWlEVHBVeW9JYXp0Vkc3YkNxdks2X1VhQWkxN2NhZjF1d3Z6NmFsQXBIZ2xobzVQdlJvWHpadDlFVlF6MjhTZ1U3c3F0TnU4WmR2QlFORUR2MHEwV0Z2OF9leG9FPSIsImxvY2FsZSI6Im5sLU5MIn0.HatOyxHBqFjYXRb1DfaPWVZGwN3RQ3R_BTZEmKqge6eonxaDLgBCBMTUwaKppj7DtnLII4-DkIzKxj-LeP0sfMkqlpFoQKJTMPX2bidZr0_FwlQ7Dm1Mxd284EQqx132HK0Xke4jjqXxE7elR7iZYDjnDoYnXl85PkjEBMcYsSHRj0ibWvH1ChkGyXpEgfwCy4uqQYRM7iOF3-A6dvgV5ti9kSkcxP5IK_7Z7SRDuhbxMEdL_ON3eJdErs7HraxGowL_HlncKnwSZO82KHObUKpZeLvdSA4CHAiCmnyFlunCMOsH5hWM99ys00rEEMvha3AsXFhLTm5uRmmoA2nwvCR5BR4tu3olhm0NG9PAuWny2rmbCrFtz739-WOX1lzP6Xxuo6cC4lU_gy2AkI3QYtQ2Hj-rRQ-3peZcBpQ49nS-VNCnrMjLo6S2BW4I6SYamN3-0mhqFSnyUZ9YiQbwaLhmJJqXzou-kFuvtY6OX_afm5deh8CfFUO03O6C0bVJ-8oSC61QAEIEdNaJR0Vb2dqAM9qAJWPP-SNr_dqte9eCV05POf0XT0ZkjtHmrM678fzIjE-tGJSN-LrumrYXZU8zVTqNBw57sDhuUROhQLDSeqoLbKJHkoQYSFIMWlouhanAegSuHFzZRmb8SkHhZ0bLyUZkFM9Rvozy21M2YKU%AMSTERDAMAPP%eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NjAzNjY0MjYsImV4cCI6MTc2MDM3MDAyNiwicm9sZXMiOlsiUk9MRV9WSVNJVE9SX1NTUCJdfQ.amWX37X4GFuflBT8HWEQtr4G1PGjQnhAwo55XKSyV7Y"
        )
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
        self.assertEqual(response.data[0]["parking_machine_favorite"], "10526")
        self.assertEqual(response.data[0]["permit_type"], "Bezoekersvergunning")
        self.assertEqual(response.data[0]["visitor_account"]["seconds_remaining"], 3600)


class TestParkingPermitZoneView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.permit_id = "1003"
        self.url = reverse("parking-permit-zone", args=[self.permit_id])
        self.mock_response = permit.MOCK_RESPONSE_VISITOR_HOLDER

    def test_success(self):
        url_template = SSPEndpoint.PERMIT.value
        url = URITemplate(url_template).expand(permit_id=self.permit_id)
        resp = respx.get(url).mock(
            return_value=httpx.Response(200, json=self.mock_response)
        )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)

    @override_settings(SSP_API_TIMEOUT_SECONDS=0.01)
    def test_timeout_and_recovery(self):
        async def slow_upstream(_r) -> httpx.Response:
            await anyio.sleep(1)
            return httpx.Response(200, json=self.mock_response)

        url_template = SSPEndpoint.PERMIT.value
        url = URITemplate(url_template).expand(permit_id=self.permit_id)
        respx.get(url).mock(
            side_effect=[slow_upstream, httpx.Response(200, json=self.mock_response)]
        )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)


class TestParkingPermitZoneByMachineView(BaseSSPTestCase):
    def setUp(self):
        super().setUp()
        self.permit_id = "1003"
        self.url = reverse(
            "parking-permit-zone-by-machine", args=[self.permit_id, 1000]
        )
        self.mock_response_without_rate = parking_zone_by_machine.MOCK_RESPONSE_NO_RATE
        self.mock_response_with_rate = parking_zone_by_machine.MOCK_RESPONSE_WITH_RATE

    # TODO: change last check if value of hourly rate has been updated
    def test_success_with_rate(self):
        resp = respx.post(SSPEndpointExternal.PARKING_ZONE_BY_MACHINE.value).mock(
            return_value=httpx.Response(200, json=self.mock_response_with_rate)
        )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
        # self.assertEqual(response.data["hourly_rate"], "€6,73")
        self.assertEqual(response.data["hourly_rate"], None)

    def test_success_without_rate(self):
        resp = respx.post(SSPEndpointExternal.PARKING_ZONE_BY_MACHINE.value).mock(
            return_value=httpx.Response(200, json=self.mock_response_without_rate)
        )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
        self.assertEqual(response.data["hourly_rate"], None)

    def test_format_machine_time_string(self):
        view = ParkingPermitZoneByMachineView()

        # Test with leading zeros
        self.assertEqual(view._format_machine_time("0900"), "09:00")
        self.assertEqual(view._format_machine_time("0059"), "00:59")
        # Test without leading zeros
        self.assertEqual(view._format_machine_time("900"), "09:00")
        self.assertEqual(view._format_machine_time("59"), "00:59")

    def test_format_machine_time_int(self):
        view = ParkingPermitZoneByMachineView()

        self.assertEqual(view._format_machine_time(900), "09:00")
        self.assertEqual(view._format_machine_time(59), "00:59")
        self.assertEqual(view._format_machine_time(2359), "23:59")
        self.assertEqual(view._format_machine_time(945), "09:45")

    def test_interpret_days_integer(self):
        view = ParkingPermitZoneByMachineView()

        # Test with time frames for all days
        days = view._interpret_days(parking_zone_by_machine.MOCK_RESPONSE_NO_RATE)
        expected_days = [
            {"day_of_week": "Maandag", "end_time": "24:00", "start_time": "09:00"},
            {"day_of_week": "Dinsdag", "end_time": "24:00", "start_time": "09:00"},
            {"day_of_week": "Woensdag", "end_time": "24:00", "start_time": "09:00"},
            {"day_of_week": "Donderdag", "end_time": "24:00", "start_time": "09:00"},
            {"day_of_week": "Vrijdag", "end_time": "24:00", "start_time": "09:00"},
            {"day_of_week": "Zaterdag", "end_time": "24:00", "start_time": "09:00"},
            {"day_of_week": "Zondag", "end_time": "24:00", "start_time": "12:00"},
        ]
        self.assertEqual(days, expected_days)

    def test_interpret_days_no_sunday(self):
        view = ParkingPermitZoneByMachineView()

        # Test with time frames for all days
        days = view._interpret_days(parking_zone_by_machine.MOCK_RESPONSE_SUNDAY_FREE)
        expected_days = [
            {"day_of_week": "Maandag", "end_time": "24:00", "start_time": "09:00"},
            {"day_of_week": "Dinsdag", "end_time": "24:00", "start_time": "09:00"},
            {"day_of_week": "Woensdag", "end_time": "24:00", "start_time": "09:00"},
            {"day_of_week": "Donderdag", "end_time": "24:00", "start_time": "09:00"},
            {"day_of_week": "Vrijdag", "end_time": "24:00", "start_time": "09:00"},
            {"day_of_week": "Zaterdag", "end_time": "24:00", "start_time": "09:00"},
        ]
        self.assertEqual(days, expected_days)

    def test_interpret_days_string(self):
        view = ParkingPermitZoneByMachineView()

        # Test with time frames for all days
        days = view._interpret_days(parking_zone_by_machine.MOCK_RESPONSE_WITH_RATE)
        expected_days = [
            {"day_of_week": "Maandag", "end_time": "20:59", "start_time": "09:00"},
            {"day_of_week": "Dinsdag", "end_time": "20:59", "start_time": "09:00"},
            {"day_of_week": "Woensdag", "end_time": "20:59", "start_time": "09:00"},
            {"day_of_week": "Donderdag", "end_time": "20:59", "start_time": "09:00"},
            {"day_of_week": "Vrijdag", "end_time": "20:59", "start_time": "09:00"},
            {"day_of_week": "Zaterdag", "end_time": "20:59", "start_time": "09:00"},
            {"day_of_week": "Zondag", "end_time": "20:59", "start_time": "09:00"},
        ]
        self.assertEqual(days, expected_days)
