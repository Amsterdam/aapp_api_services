from unittest.mock import patch

import responses
from django.conf import settings
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status

from contact.enums.base import ModuleSourceChoices, ServiceClass
from contact.enums.kingsday_land import KingsdayLandProperties
from contact.enums.kingsday_water import KingsdayWaterProperties
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
    kid_flea_market,
    park_and_ride,
    recycle_boat,
    recycle_drop_off,
    toilet,
)
from core.tests.test_authentication import ResponsesActivatedAPITestCase


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}},
)
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


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}},
)
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

    def test_kingsday_land_layers(self):
        cases = [
            {
                "label": "Evenement",
                "code": 1,
                "icon_label": "event",
                "url": f"{settings.KINGSDAY_URL}1.json",
                "mock": events.MOCK_DATA,
                "expected_features": len(events.MOCK_DATA["features"]),
            },
            {
                "label": "EHBO-post",
                "code": 2,
                "icon_label": "first_aid",
                "url": f"{settings.KINGSDAY_URL}2.json",
                "mock": first_aid.MOCK_DATA,
                "expected_features": len(first_aid.MOCK_DATA["features"]),
            },
            {
                "label": "Inleverpunt overgebleven spullen",
                "code": 3,
                "icon_label": "recycle_drop_off",
                "url": f"{settings.KINGSDAY_URL}3.json",
                "mock": recycle_drop_off.MOCK_DATA,
                "expected_features": len(recycle_drop_off.MOCK_DATA["features"]),
            },
            {
                "label": "Toilet",
                "code": 4,
                "icon_label": "toilet",
                "url": f"{settings.KINGSDAY_URL}4.json",
                "mock": toilet.MOCK_DATA,
                "expected_features": len(toilet.MOCK_DATA["features"]),
            },
            {
                "label": "Omleiding",
                "code": 5,
                "icon_label": "detour",
                "url": f"{settings.KINGSDAY_URL}5.json",
                "mock": detour.MOCK_DATA,
                "expected_features": len(detour.MOCK_DATA["features"]),
            },
            {
                "label": "Afgesloten parkeergarage",
                "code": 6,
                "icon_label": "closed_parking_lot",
                "url": f"{settings.KINGSDAY_URL}6.json",
                "mock": closed_parking_lot.MOCK_DATA,
                "expected_features": len(closed_parking_lot.MOCK_DATA["features"]),
            },
            {
                "label": "Drinkwater",
                "code": 0,
                "icon_label": "drink_water",
                "url": settings.TAP_URL,
                "mock": taps.MOCK_DATA,
                "expected_features": 3,  # one mock tap is outside Amsterdam municipality
            },
            {
                "label": "P+R",
                "code": 7,
                "icon_label": "park_and_ride",
                "url": f"{settings.KINGSDAY_URL}7.json",
                "mock": park_and_ride.MOCK_DATA,
                "expected_features": len(park_and_ride.MOCK_DATA["features"]),
            },
            {
                "label": "Kindervrijmarkt",
                "code": 8,
                "icon_label": "kid_flea_market",
                "url": f"{settings.KINGSDAY_URL}8.json",
                "mock": kid_flea_market.MOCK_DATA,
                "expected_features": len(kid_flea_market.MOCK_DATA["features"]),
            },
        ]

        for case in cases:
            with self.subTest(layer=case["label"]):
                with patch(
                    "contact.services.kingsday_land.KingsdayLandData.choices_as_list",
                    return_value=[
                        {
                            "label": case["label"],
                            "code": case["code"],
                            "icon_label": case["icon_label"],
                        }
                    ],
                ):
                    responses.get(case["url"], json=case["mock"])

                    response = self.client.get(
                        reverse("service-map", kwargs={"service_id": 3}),
                        headers=self.api_headers,
                    )

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                payload = response.json()

                self.assertEqual(
                    payload["properties_to_include"],
                    KingsdayLandProperties.choices_as_list(),
                )
                self.assertEqual(
                    len(payload["data"]["features"]),
                    case["expected_features"],
                )

    def test_kingsday_water_layers(self):
        cases = [
            {
                "label": "Invaarverbod",
                "code": 9,
                "icon_label": "boating_ban",
                "mock": boating_ban.MOCK_DATA,
            },
            {
                "label": "Afsluiting",
                "code": 10,
                "icon_label": "boat_block",
                "mock": boat_block.MOCK_DATA,
            },
            {
                "label": "Afvalboot",
                "code": 11,
                "icon_label": "recycle_boat",
                "mock": recycle_boat.MOCK_DATA,
            },
            {
                "label": "Vaarrichting",
                "code": 12,
                "icon_label": "boat_direction",
                "mock": direction.MOCK_DATA,
            },
        ]

        for case in cases:
            with self.subTest(layer=case["label"]):
                with patch(
                    "contact.services.kingsday_water.KingsdayWaterData.choices_as_list",
                    return_value=[
                        {
                            "label": case["label"],
                            "code": case["code"],
                            "icon_label": case["icon_label"],
                        }
                    ],
                ):
                    responses.get(
                        f"{settings.KINGSDAY_URL}{case['code']}.json", json=case["mock"]
                    )

                    response = self.client.get(
                        reverse("service-map", kwargs={"service_id": 4}),
                        headers=self.api_headers,
                    )

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                payload = response.json()
                self.assertEqual(
                    payload["properties_to_include"],
                    KingsdayWaterProperties.choices_as_list(),
                )
                self.assertEqual(
                    len(payload["data"]["features"]),
                    len(case["mock"]["features"]),
                )

    def test_kingsday_land_drinkwater_filters_title_and_geometry(self):
        with patch(
            "contact.services.kingsday_land.KingsdayLandData.choices_as_list",
            return_value=[{"label": "Drinkwater", "code": 0, "icon_label": "tap"}],
        ):
            responses.get(settings.TAP_URL, json=taps.MOCK_DATA)

            response = self.client.get(
                reverse("service-map", kwargs={"service_id": 3}),
                headers=self.api_headers,
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()

        features = payload["data"]["features"]

        expected_taps = [
            tap
            for tap in taps.MOCK_DATA["features"]
            if tap.get("properties", {}).get("plaats")
            in ["Amsterdam", "Weesp", "Amsterdamse bos"]
        ]
        expected_titles = []
        expected_coords = []
        for tap in expected_taps:
            properties = tap.get("properties", {})
            expected_titles.append(
                "Drinkfontein"
                if "fontein" in (properties.get("beschrijvi") or "").lower()
                else "Watertap"
            )
            expected_coords.append(
                [properties.get("longitude"), properties.get("latitude")]
            )

        self.assertEqual(len(features), len(expected_taps))
        self.assertEqual(
            [f["properties"].get("aapp_title") for f in features],
            expected_titles,
        )
        self.assertEqual(
            [f["geometry"].get("coordinates") for f in features],
            expected_coords,
        )

        for feature in features:
            self.assertEqual(feature["geometry"].get("type"), "Point")
            self.assertEqual(feature["properties"].get("aapp_subtitle"), "Drinkwater")
            self.assertIsNone(feature["properties"].get("aapp_address"))

    def test_kingsday_land_omleiding_polygon_has_fill_opacity_stroke_and_stroke_width(
        self,
    ):
        with patch(
            "contact.services.kingsday_land.KingsdayLandData.choices_as_list",
            return_value=[{"label": "Omleiding", "code": 5, "icon_label": "detour"}],
        ):
            responses.get(f"{settings.KINGSDAY_URL}5.json", json=detour.MOCK_DATA)
            response = self.client.get(
                reverse("service-map", kwargs={"service_id": 3}),
                headers=self.api_headers,
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()

        polygon_features = [
            f
            for f in payload["data"]["features"]
            if f.get("geometry", {}).get("type") in ["Polygon", "MultiPolygon"]
        ]
        self.assertTrue(polygon_features)

        props = polygon_features[0]["properties"]
        self.assertEqual(props.get("fill"), "#EC0000")
        self.assertEqual(props.get("fill-opacity"), 0.2)
        self.assertEqual(props.get("stroke"), "#EC0000")
        self.assertEqual(props.get("stroke-width"), 2)

    def test_kingsday_land_toilet_meta_becomes_key_value_table(self):
        with patch(
            "contact.services.kingsday_land.KingsdayLandData.choices_as_list",
            return_value=[{"label": "Toilet", "code": 4, "icon_label": "toilet"}],
        ):
            responses.get(f"{settings.KINGSDAY_URL}4.json", json=toilet.MOCK_DATA)
            response = self.client.get(
                reverse("service-map", kwargs={"service_id": 3}),
                headers=self.api_headers,
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        features = payload["data"]["features"]
        self.assertTrue(features)

        props = features[0]["properties"]
        self.assertEqual(
            props.get("aapp_toilet_table"),
            [
                {"key": "Sta-toilet (4x)", "value": "1"},
                {"key": "Zit-toilet", "value": "1"},
            ],
        )

    def test_service_without_dataservice_returns_404(self):
        with patch(
            "contact.views.service_views.Services.get_service_by_id",
            return_value=ServiceClass(
                id=999,
                title="No data",
                icon="x",
                input_module=ModuleSourceChoices.HANDIG_IN_DE_STAD.value,
                dataservice=None,
            ),
        ):
            response = self.client.get(
                reverse("service-map", kwargs={"service_id": 999}),
                headers=self.api_headers,
            )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.json().get("detail"), "No data service available for this service."
        )

    def test_not_implemented_get_service_map_view(self):
        response = self.client.get(
            reverse("service-map", kwargs={"service_id": 999}),
            headers=self.api_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Service not found.")
