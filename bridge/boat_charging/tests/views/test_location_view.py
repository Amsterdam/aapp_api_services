from urllib.parse import urljoin

import httpx
import respx
from django.conf import settings
from django.urls import reverse

from bridge.boat_charging.tests.mock_data import (
    charging_station_detail,
    location_detail,
    locations,
    tariff_detail,
)
from bridge.boat_charging.tests.views.base_view import BoatChargingTestCase


class TestLocationView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-locations")

    def test_success(self):
        resp = respx.get(settings.BOAT_CHARGING_ENDPOINTS["LOCATIONS"]).mock(
            return_value=httpx.Response(200, json=locations.MOCK_RESPONSE)
        )
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)


class TestLocationDetailView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.location_id = "foobar"
        self.url = reverse(
            "boat-charging-location-detail", kwargs={"location_id": self.location_id}
        )

    def test_success(self):
        ext_endpoint = urljoin(
            settings.BOAT_CHARGING_ENDPOINTS["LOCATIONS"], self.location_id
        )
        resp = respx.get(ext_endpoint).mock(
            return_value=httpx.Response(200, json=location_detail.MOCK_RESPONSE)
        )

        tariff_endpoint = urljoin(
            settings.BOAT_CHARGING_ENDPOINTS["TARIFFS"],
            "NLSGMTRYXYMXMPAOXJFEYLQXIHAYXJPNTOY",
        )
        resp_tariff = respx.get(tariff_endpoint).mock(
            return_value=httpx.Response(200, json=tariff_detail.MOCK_RESPONSE)
        )

        for charging_station_id in ["cs_id_1", "cs_id_2"]:
            charging_station_endpoint = urljoin(
                settings.BOAT_CHARGING_ENDPOINTS["CHARGING_STATIONS"],
                charging_station_id,
            )
            respx.get(charging_station_endpoint).mock(
                return_value=httpx.Response(
                    200, json=charging_station_detail.MOCK_RESPONSE
                )
            )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
        self.assertEqual(resp_tariff.call_count, 1)
        self.assertEqual(len(response["charging_stations"]), 2)
