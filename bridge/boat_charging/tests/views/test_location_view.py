import httpx
import respx
from django.conf import settings
from django.urls import reverse

from bridge.boat_charging.tests.mock_data import (
    charging_station_detail,
    charging_stations,
    location_detail,
    locations,
    tariff_detail,
)
from bridge.boat_charging.tests.views.base_view import BoatChargingTestCase
from bridge.boat_charging.views.location_view import LocationView


class TestLocationView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-locations")
        self.view = LocationView.as_view()

    def test_success(self):
        resp = respx.get(settings.BOAT_CHARGING_ENDPOINTS["LOCATIONS"]).mock(
            return_value=httpx.Response(200, json=locations.MOCK_RESPONSE)
        )
        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)

        # check that the address is returned in the expected format
        self.assertEqual("address" in response.data["features"][0]["properties"], True)
        self.assertEqual(
            response.data["features"][0]["properties"]["address"],
            {
                "street": "Transformatorweg",
                "number": "104",
                "postcode": "1234 AM",
                "city": "Amsterdam",
                "coordinates": {
                    "lat": 52.387313,
                    "lon": 4.822313,
                },
            },
        )

        # location 2 (AmsterdamBoatTest1) has two charging stations, one operative and one offline station -> "OPERATIVE"
        self.assertEqual(
            response.data["features"][1]["properties"]["status"], "OPERATIVE"
        )
        # location 3 (AmsterdamBoatTest3) has one occupied station -> "OCCUPIED"
        self.assertEqual(
            response.data["features"][2]["properties"]["status"], "OCCUPIED"
        )

    def test_location_status_mapping(self):

        resp_charging_stations = respx.get(
            settings.BOAT_CHARGING_ENDPOINTS["CHARGING_STATIONS"]
        ).mock(return_value=httpx.Response(200, json=charging_stations.MOCK_RESPONSE))

        status_mapping = self.view.get_location_statuses()

        self.assertEqual(resp_charging_stations.call_count, 1)
        self.assertEqual(
            status_mapping["2c0ccfb795d040e39136b7dd1d25f13e"], "OPERATIVE"
        )
        self.assertEqual(status_mapping["a9d9b42ce3eb4d8cbf50bb6aaeaa6357"], "OCCUPIED")


class TestLocationDetailView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.location_id = "foobar"
        self.url = reverse(
            "boat-charging-location-detail", kwargs={"location_id": self.location_id}
        )

    def test_success(self):
        ext_endpoint = (
            f"{settings.BOAT_CHARGING_ENDPOINTS['LOCATIONS']}/{self.location_id}"
        )
        resp = respx.get(ext_endpoint).mock(
            return_value=httpx.Response(200, json=location_detail.MOCK_RESPONSE)
        )

        tariff_endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['TARIFFS']}/NLSGMTRYXYMXMPAOXJFEYLQXIHAYXJPNTOY"
        resp_tariff = respx.get(tariff_endpoint).mock(
            return_value=httpx.Response(200, json=tariff_detail.MOCK_RESPONSE)
        )

        for charging_station_id in ["cs_id_1", "cs_id_2"]:
            charging_station_endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['CHARGING_STATIONS']}/{charging_station_id}"
            respx.get(charging_station_endpoint).mock(
                return_value=httpx.Response(
                    200, json=charging_station_detail.MOCK_RESPONSE
                )
            )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
        self.assertEqual(resp_tariff.call_count, 1)
        self.assertEqual(len(response.data["charging_stations"]), 2)

    def test_unknown_location_id(self):
        ext_endpoint = (
            f"{settings.BOAT_CHARGING_ENDPOINTS['LOCATIONS']}/{self.location_id}"
        )
        resp = respx.get(ext_endpoint).mock(return_value=httpx.Response(403))

        tariff_endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['TARIFFS']}/NLSGMTRYXYMXMPAOXJFEYLQXIHAYXJPNTOY"
        resp_tariff = respx.get(tariff_endpoint).mock(
            return_value=httpx.Response(200, json=tariff_detail.MOCK_RESPONSE)
        )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(resp.call_count, 1)
        self.assertEqual(resp_tariff.call_count, 0)
