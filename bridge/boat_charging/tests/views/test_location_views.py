import httpx
import respx
from django.conf import settings
from django.urls import reverse

from bridge.boat_charging.tests.mock_data import location_detail, locations
from bridge.boat_charging.tests.views.base_view import BoatChargingTestCase
from bridge.boat_charging.views.location_view import LocationView


class TestLocationView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-locations")
        self.view = LocationView()

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
                "street": "Isolatorweg",
                "number": "178",
                "postcode": "1234 AM",
                "city": "Amsterdam",
                "coordinates": {
                    "lat": 52.327549,
                    "lon": 4.972519,
                },
            },
        )

    def test_get_status_and_kw_from_sockets_occupied(self):
        sockets = [
            {
                "chargingStationId": "ABC-7BMY2",
                "evseId": "1",
                "status": "FAULTED",
                "available": False,
                "maxElectricPower": 22.0,
            },
            {
                "chargingStationId": "ABC-IFZTY",
                "evseId": "1",
                "status": "OCCUPIED",
                "available": False,
            },
            {
                "chargingStationId": "ABC-MX1VV",
                "evseId": "1",
                "status": "UNKNOWN",
                "available": False,
            },
        ]
        status, max_kw = self.view._get_status_and_kw_from_sockets(sockets)
        self.assertEqual(status, "OCCUPIED")
        self.assertEqual(max_kw, 22.0)

    def test_get_status_and_kw_from_sockets_operative(self):
        sockets = [
            {
                "chargingStationId": "ABC-7BMY2",
                "evseId": "1",
                "status": "OPERATIVE",
                "available": True,
                "maxElectricPower": 19.0,
            },
            {
                "chargingStationId": "ABC-IFZTY",
                "evseId": "1",
                "status": "OCCUPIED",
                "available": False,
                "maxElectricPower": 22.0,
            },
            {
                "chargingStationId": "ABC-MX1VV",
                "evseId": "1",
                "status": "UNKNOWN",
                "available": False,
            },
        ]
        status, max_kw = self.view._get_status_and_kw_from_sockets(sockets)
        self.assertEqual(status, "OPERATIVE")
        self.assertEqual(max_kw, 19.0)

    def test_get_status_and_kw_from_sockets_operative_no_max_kw(self):
        sockets = [
            {
                "chargingStationId": "ABC-7BMY2",
                "evseId": "1",
                "status": "OPERATIVE",
                "available": True,
            },
            {
                "chargingStationId": "ABC-IFZTY",
                "evseId": "1",
                "status": "OCCUPIED",
                "available": False,
                "maxElectricPower": 22.0,
            },
            {
                "chargingStationId": "ABC-MX1VV",
                "evseId": "1",
                "status": "UNKNOWN",
                "available": False,
            },
        ]
        status, max_kw = self.view._get_status_and_kw_from_sockets(sockets)
        self.assertEqual(status, "OPERATIVE")
        self.assertEqual(max_kw, 22.0)

    def test_get_status_and_kw_from_sockets_inoperative(self):
        sockets = [
            {
                "chargingStationId": "ABC-7BMY2",
                "evseId": "1",
                "status": "FAULTED",
                "available": False,
                "maxElectricPower": 22.0,
            },
            {
                "chargingStationId": "ABC-IFZTY",
                "evseId": "1",
                "status": "INOPERATIVE",
                "available": False,
            },
            {
                "chargingStationId": "ABC-MX1VV",
                "evseId": "1",
                "status": "UNKNOWN",
                "available": False,
            },
        ]
        status, max_kw = self.view._get_status_and_kw_from_sockets(sockets)
        self.assertEqual(status, "INOPERATIVE")
        self.assertEqual(max_kw, 22.0)

    def test_convert_regular_hours(self):
        regular_hours = [
            {"weekday": 1, "periodBegin": "08:00", "periodEnd": "18:00"},
            {"weekday": 2, "periodBegin": "08:00", "periodEnd": "18:00"},
            {"weekday": 3, "periodBegin": "09:00", "periodEnd": "19:30"},
            {"weekday": 4, "periodBegin": "04:12", "periodEnd": "08:12"},
            {"weekday": 5, "periodBegin": "07:12", "periodEnd": "13:12"},
            {"weekday": 6, "periodBegin": "08:12", "periodEnd": "21:12"},
            {"weekday": 7, "periodBegin": "07:19", "periodEnd": "08:19"},
        ]
        converted_hours = self.view._convert_regular_hours(regular_hours)
        expected_converted_hours = [
            {
                "dayOfWeek": 1,
                "opening": {"hours": 8, "minutes": 0},
                "closing": {"hours": 18, "minutes": 0},
            },
            {
                "dayOfWeek": 2,
                "opening": {"hours": 8, "minutes": 0},
                "closing": {"hours": 18, "minutes": 0},
            },
            {
                "dayOfWeek": 3,
                "opening": {"hours": 9, "minutes": 0},
                "closing": {"hours": 19, "minutes": 30},
            },
            {
                "dayOfWeek": 4,
                "opening": {"hours": 4, "minutes": 12},
                "closing": {"hours": 8, "minutes": 12},
            },
            {
                "dayOfWeek": 5,
                "opening": {"hours": 7, "minutes": 12},
                "closing": {"hours": 13, "minutes": 12},
            },
            {
                "dayOfWeek": 6,
                "opening": {"hours": 8, "minutes": 12},
                "closing": {"hours": 21, "minutes": 12},
            },
            {
                "dayOfWeek": 0,
                "opening": {"hours": 7, "minutes": 19},
                "closing": {"hours": 8, "minutes": 19},
            },
        ]
        self.assertEqual(converted_hours, expected_converted_hours)

    def test_get_addr(self):
        input_str = "Tilanusstraat 10-2"
        street, number = self.view.split_address(input_str)
        self.assertEqual(street, "Tilanusstraat ")
        self.assertEqual(number, "10-2")

    def test_get_addr_2(self):
        input_str = "Amstel 1"
        street, number = self.view.split_address(input_str)
        self.assertEqual(street, "Amstel ")
        self.assertEqual(number, "1")

    def test_get_addr_3(self):
        input_str = "Retief Straat 15h/2"
        street, number = self.view.split_address(input_str)
        self.assertEqual(street, "Retief Straat ")
        self.assertEqual(number, "15h/2")

    def test_get_addr4(self):
        input_str = "Main Street 12 bis"
        street, number = self.view.split_address(input_str)
        self.assertEqual(street, "Main Street ")
        self.assertEqual(number, "12 bis")

    def test_get_addr5(self):
        input_str = "Kraanspoor 7L3"
        street, number = self.view.split_address(input_str)
        self.assertEqual(street, "Kraanspoor ")
        self.assertEqual(number, "7L3")

    def test_split_address_without_number_returns_original_address(self):
        input_str = "NDSM-Plein"
        street, number = self.view.split_address(input_str)
        self.assertEqual(street, "NDSM-Plein")
        self.assertEqual(number, "")


class TestLocationDetailView(BoatChargingTestCase):
    def setUp(self):
        super().setUp()
        self.location_id = "foobar"
        self.url = reverse(
            "boat-charging-location-detail", kwargs={"location_id": self.location_id}
        )
        self.external_endpoint = (
            f"{settings.BOAT_CHARGING_ENDPOINTS['LOCATIONS']}/{self.location_id}"
        )

    def test_success(self):

        resp = respx.get(self.external_endpoint).mock(
            return_value=httpx.Response(200, json=location_detail.MOCK_RESPONSE)
        )

        response = self.client.get(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)

    def test_forbidden_from_upstream_is_mapped_to_not_found(self):

        respx.get(self.external_endpoint).mock(
            return_value=httpx.Response(403, json={})
        )

        response = self.client.get(self.url, headers=self.api_headers)

        self.assertEqual(response.status_code, 404)

    def test_invalid_location_id_returns_400(self):
        invalid_url = reverse(
            "boat-charging-location-detail",
            kwargs={"location_id": "invalid$id"},
        )

        response = self.client.get(invalid_url, headers=self.api_headers)

        self.assertEqual(response.status_code, 400)
