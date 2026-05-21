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
        self.view = LocationView()

    def _setup_mock_location_response(self):
        resp = respx.get(settings.BOAT_CHARGING_ENDPOINTS["LOCATIONS"]).mock(
            return_value=httpx.Response(200, json=locations.MOCK_RESPONSE)
        )
        resp_charging_stations = respx.get(
            settings.BOAT_CHARGING_ENDPOINTS["CHARGING_STATIONS"]
        ).mock(return_value=httpx.Response(200, json=charging_stations.MOCK_RESPONSE))
        response = self.client.get(self.url, headers=self.api_headers)
        return resp, resp_charging_stations, response

    def test_success_basic_params(self):
        resp, resp_charging_stations, response = self._setup_mock_location_response()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
        self.assertEqual(resp_charging_stations.call_count, 1)

    def test_success_address_format(self):
        _, _, response = self._setup_mock_location_response()
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

    def test_determine_overall_status_and_wattage(self):

        location_connectors = {
            "loc_1": [("OPERATIVE", 22), ("OCCUPIED", 11)],
            "loc_2": [("OCCUPIED", 22), ("INOPERATIVE", 11)],
            "loc_3": [("INOPERATIVE", 22), ("INOPERATIVE", 11)],
            "loc_4": [("OCCUPIED", 22), ("OPERATIVE", 11)],
            "loc_5": [("OCCUPIED", 22), ("OCCUPIED", 11)],
        }
        result = self.view.determine_overall_status_and_wattage(location_connectors)
        expected_result = {
            "loc_1": {"status": "OPERATIVE", "max_kw": 0.022},
            "loc_2": {"status": "INOPERATIVE", "max_kw": 0.022},
            "loc_3": {"status": "INOPERATIVE", "max_kw": 0.022},
            "loc_4": {"status": "OPERATIVE", "max_kw": 0.011},
            "loc_5": {"status": "OCCUPIED", "max_kw": 0.022},
        }
        self.assertEqual(result, expected_result)

    def test_determine_overall_status_and_wattage_missing_wattage(self):
        # this is the situation on the staging environment on 21-05-2026
        location_connectors = {
            "loc_1": [("INOPERATIVE", 2200), ("UNKNOWN", None)],
            "loc_3": [("OCCUPIED", None)],
        }
        result = self.view.determine_overall_status_and_wattage(location_connectors)
        expected_result = {
            "loc_1": {"status": "INOPERATIVE", "max_kw": 2.2},
            "loc_3": {"status": "OCCUPIED", "max_kw": None},
        }
        self.assertEqual(result, expected_result)


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

        respx.get(settings.BOAT_CHARGING_ENDPOINTS["CHARGING_STATIONS"]).mock(
            return_value=httpx.Response(200, json=charging_stations.MOCK_RESPONSE)
        )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
        self.assertEqual(resp_tariff.call_count, 1)
        self.assertEqual(len(response.data["charging_stations"]), 2)
        self.assertEqual(response.data["max_kw"], None)
        self.assertEqual(response.data["status"], "UNKNOWN")

    def test_no_tariff(self):
        ext_endpoint = (
            f"{settings.BOAT_CHARGING_ENDPOINTS['LOCATIONS']}/{self.location_id}"
        )
        resp = respx.get(ext_endpoint).mock(
            return_value=httpx.Response(
                200, json=location_detail.MOCK_RESPONSE_NO_TARIFF
            )
        )

        for charging_station_id in ["cs_id_1", "cs_id_2"]:
            charging_station_endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['CHARGING_STATIONS']}/{charging_station_id}"
            respx.get(charging_station_endpoint).mock(
                return_value=httpx.Response(
                    200, json=charging_station_detail.MOCK_RESPONSE
                )
            )

        respx.get(settings.BOAT_CHARGING_ENDPOINTS["CHARGING_STATIONS"]).mock(
            return_value=httpx.Response(200, json=charging_stations.MOCK_RESPONSE)
        )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
        self.assertEqual(response.data["tariff"], None)
        self.assertEqual(len(response.data["charging_stations"]), 2)

    def test_tariff_not_accessible(self):
        ext_endpoint = (
            f"{settings.BOAT_CHARGING_ENDPOINTS['LOCATIONS']}/{self.location_id}"
        )
        resp = respx.get(ext_endpoint).mock(
            return_value=httpx.Response(200, json=location_detail.MOCK_RESPONSE)
        )

        tariff_endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['TARIFFS']}/NLSGMTRYXYMXMPAOXJFEYLQXIHAYXJPNTOY"
        resp_tariff = respx.get(tariff_endpoint).mock(return_value=httpx.Response(403))

        for charging_station_id in ["cs_id_1", "cs_id_2"]:
            charging_station_endpoint = f"{settings.BOAT_CHARGING_ENDPOINTS['CHARGING_STATIONS']}/{charging_station_id}"
            respx.get(charging_station_endpoint).mock(
                return_value=httpx.Response(
                    200, json=charging_station_detail.MOCK_RESPONSE
                )
            )

        respx.get(settings.BOAT_CHARGING_ENDPOINTS["CHARGING_STATIONS"]).mock(
            return_value=httpx.Response(200, json=charging_stations.MOCK_RESPONSE)
        )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
        self.assertEqual(resp_tariff.call_count, 1)
        self.assertEqual(response.data["tariff"], None)
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
