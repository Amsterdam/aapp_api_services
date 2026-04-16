from unittest.mock import patch

import responses
from django.conf import settings
from django.urls import reverse
from rest_framework import status

from contact.enums.kingsday_land import KingsdayLandProperties
from contact.enums.services import Services
from contact.enums.taps import TapFilters, TapProperties
from contact.enums.toilets import ToiletFilters, ToiletProperties
from contact.tests.mock_data import taps, toilets
from contact.tests.mock_data.kingsday import (
    boat_block,
    boating_ban,
    closed_parking_lot,
    detour,
    direction,
    events,
    first_aid,
    park_and_ride,
    recycle_boat,
    recycle_drop_off,
    toilet,
)
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class TestServiceMapsView(ResponsesActivatedAPITestCase):
    def test_success_get_service_maps_view_no_module_source(self):

        url = reverse("service-maps")
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        # by default, the module_source should be "handig-in-de-stad", so we should only get the services with that input_module
        expected_services = [
            service
            for service in Services.choices_as_list()
            if service["input_module"] == "handig-in-de-stad"
        ]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(expected_services))
        self.assertEqual(
            sorted(s["title"] for s in response.data),
            sorted(s["title"] for s in expected_services),
        )

    def test_success_get_service_maps_view_handig_in_de_stad(self):
        url = reverse("service-maps")
        data = {"module_source": "handig-in-de-stad"}
        response = self.client.get(
            url,
            data,
            headers=self.api_headers,
        )

        expected_services = [
            service
            for service in Services.choices_as_list()
            if service["input_module"] == "handig-in-de-stad"
        ]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(expected_services))
        self.assertEqual(
            sorted(s["title"] for s in response.data),
            sorted(s["title"] for s in expected_services),
        )

    def test_success_get_service_maps_view_koningsdag(self):
        url = reverse("service-maps")
        data = {"module_source": "koningsdag"}
        response = self.client.get(url, data, headers=self.api_headers)
        expected_services = [
            service
            for service in Services.choices_as_list()
            if service["input_module"] == "koningsdag"
        ]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(expected_services))
        self.assertEqual(
            sorted(s["title"] for s in response.data),
            sorted(s["title"] for s in expected_services),
        )

    def test_success_get_service_maps_view_invalid(self):
        url = reverse("service-maps")
        data = {"module_source": "invalid_module"}
        response = self.client.get(url, data, headers=self.api_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestServiceMapView(ResponsesActivatedAPITestCase):
    def test_success_get_service_map_view_toilets(self):
        # Mock the response from the external API
        responses.get(settings.PUBLIC_TOILET_URL, json=toilets.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 1})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["filters"], ToiletFilters.choices_as_list())
        self.assertEqual(
            response.data["properties_to_include"], ToiletProperties.choices_as_list()
        )
        self.assertEqual(
            len(response.data["data"]["features"]), len(toilets.MOCK_DATA["features"])
        )

    def test_success_get_service_map_view_taps(self):
        # Mock the response from the external API
        responses.get(settings.TAP_URL, json=taps.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 2})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["filters"], TapFilters.choices_as_list())
        self.assertEqual(
            response.data["properties_to_include"], TapProperties.choices_as_list()
        )

    @patch(
        "contact.services.kingsday_land.KingsdayLandData.choices_as_list",
        return_value=[{"label": "Evenement", "code": 1, "icon_label": "event"}],
    )
    def test_success_get_service_map_view_kingsday_land_events(self, mock_data_layers):
        # Mock the response from the external API
        url = f"{settings.KINGSDAY_URL}1.json"
        responses.get(url, json=events.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 3})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["properties_to_include"],
            KingsdayLandProperties.choices_as_list(),
        )

    @patch(
        "contact.services.kingsday_land.KingsdayLandData.choices_as_list",
        return_value=[{"label": "EHBO-post", "code": 2, "icon_label": "first_aid"}],
    )
    def test_success_get_service_map_view_kingsday_land_first_aid(
        self, mock_data_layers
    ):
        # Mock the response from the external API
        url = f"{settings.KINGSDAY_URL}2.json"
        responses.get(url, json=first_aid.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 3})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch(
        "contact.services.kingsday_land.KingsdayLandData.choices_as_list",
        return_value=[
            {
                "label": "Inleverpunt overgebleven spullen",
                "code": 3,
                "icon_label": "recycle_drop_off",
            }
        ],
    )
    def test_success_get_service_map_view_kingsday_land_leftover_stuff(
        self, mock_data_layers
    ):
        # Mock the response from the external API
        url = f"{settings.KINGSDAY_URL}3.json"
        responses.get(url, json=recycle_drop_off.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 3})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch(
        "contact.services.kingsday_land.KingsdayLandData.choices_as_list",
        return_value=[{"label": "Toilet", "code": 4, "icon_label": "toilet"}],
    )
    def test_success_get_service_map_view_kingsday_land_toilet(self, mock_data_layers):
        # Mock the response from the external API
        url = f"{settings.KINGSDAY_URL}4.json"
        responses.get(url, json=toilet.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 3})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch(
        "contact.services.kingsday_land.KingsdayLandData.choices_as_list",
        return_value=[{"label": "Omleiding", "code": 5, "icon_label": "detour"}],
    )
    def test_success_get_service_map_view_kingsday_land_detour(self, mock_data_layers):
        # Mock the response from the external API
        url = f"{settings.KINGSDAY_URL}5.json"
        responses.get(url, json=detour.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 3})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch(
        "contact.services.kingsday_land.KingsdayLandData.choices_as_list",
        return_value=[
            {
                "label": "Afgesloten parkeergarage",
                "code": 6,
                "icon_label": "closed_parking_lot",
            }
        ],
    )
    def test_success_get_service_map_view_kingsday_land_closed_parking_lot(
        self, mock_data_layers
    ):
        # Mock the response from the external API
        url = f"{settings.KINGSDAY_URL}6.json"
        responses.get(url, json=closed_parking_lot.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 3})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch(
        "contact.services.kingsday_land.KingsdayLandData.choices_as_list",
        return_value=[
            {
                "label": "Drinkwater",
                "code": 0,
                "icon_label": "drink_water",
            }
        ],
    )
    def test_success_get_service_map_view_kingsday_land_drink_water(
        self, mock_data_layers
    ):
        # Mock the response from the external API
        url = f"{settings.TAP_URL}"
        responses.get(url, json=taps.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 3})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch(
        "contact.services.kingsday_land.KingsdayLandData.choices_as_list",
        return_value=[
            {
                "label": "P+R",
                "code": 61,
                "icon_label": "park_and_ride",
            }
        ],
    )
    def test_success_get_service_map_view_kingsday_land_park_and_ride(
        self, mock_data_layers
    ):
        # Mock the response from the external API
        url = f"{settings.KINGSDAY_URL}61.json"
        responses.get(url, json=park_and_ride.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 3})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch(
        "contact.services.kingsday_water.KingsdayWaterData.choices_as_list",
        return_value=[
            {
                "label": "Invaarverbod",
                "code": 7,
                "icon_label": "boating_ban",
            }
        ],
    )
    def test_success_get_service_map_view_kingsday_water_boating_ban(
        self, mock_data_layers
    ):
        # Mock the response from the external API
        url = f"{settings.KINGSDAY_URL}7.json"
        responses.get(url, json=boating_ban.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 4})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch(
        "contact.services.kingsday_water.KingsdayWaterData.choices_as_list",
        return_value=[
            {
                "label": "Afsluiting",
                "code": 8,
                "icon_label": "boat_block",
            }
        ],
    )
    def test_success_get_service_map_view_kingsday_water_boat_block(
        self, mock_data_layers
    ):
        # Mock the response from the external API
        url = f"{settings.KINGSDAY_URL}8.json"
        responses.get(url, json=boat_block.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 4})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch(
        "contact.services.kingsday_water.KingsdayWaterData.choices_as_list",
        return_value=[
            {
                "label": "Afvalboot",
                "code": 9,
                "icon_label": "recycle_boat",
            }
        ],
    )
    def test_success_get_service_map_view_kingsday_water_recycle_boat(
        self, mock_data_layers
    ):
        # Mock the response from the external API
        url = f"{settings.KINGSDAY_URL}9.json"
        responses.get(url, json=recycle_boat.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 4})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch(
        "contact.services.kingsday_water.KingsdayWaterData.choices_as_list",
        return_value=[
            {
                "label": "Vaarrichting",
                "code": 10,
                "icon_label": "boat_direction",
            }
        ],
    )
    def test_success_get_service_map_view_kingsday_water_boat_direction(
        self, mock_data_layers
    ):
        # Mock the response from the external API
        url = f"{settings.KINGSDAY_URL}10.json"
        responses.get(url, json=direction.MOCK_DATA)

        url = reverse("service-map", kwargs={"service_id": 4})
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_not_implemented_get_service_map_view(self):
        # Mock the response from the external API

        url = reverse(
            "service-map", kwargs={"service_id": 999}
        )  # Non-existing service_id
        response = self.client.get(
            url,
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Service not found.")
