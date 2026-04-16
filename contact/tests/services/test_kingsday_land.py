import responses
from django.conf import settings

from contact.enums.kingsday_land import (
    KingsdayLandFilters,
    KingsdayLandIcons,
    KingsdayLandProperties,
)
from contact.services.kingsday_land import KingsdayLandService
from contact.tests.mock_data.kingsday import events, first_aid
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class KingsdayLandServiceTest(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.service = KingsdayLandService()

    def test_get_full_data(self):
        self.service.data_layers = [
            {"label": "Evenement", "code": 1, "icon_label": "event"}
        ]

        url = f"{self.service.data_url}{self.service.data_layers[0]['code']}.json"

        responses.get(url, json=events.MOCK_DATA)
        full_data = self.service.get_full_data()
        self.assertEqual(full_data["filters"], KingsdayLandFilters.choices_as_list())
        self.assertEqual(
            full_data["properties_to_include"], KingsdayLandProperties.choices_as_list()
        )
        self.assertEqual(
            full_data["icons_to_include"], KingsdayLandIcons.choices_as_dict()
        )
        features = full_data["data"]["features"]
        self.assertEqual(len(features), 2)
        self.assertEqual([feature.get("id") for feature in features], [1, 2])
        self.assertTrue(
            all(
                (feature.get("properties") or {}).get("aapp_subtitle") == "Evenement"
                for feature in features
            )
        )

    def test_get_full_data_does_not_mutate_data_url(self):
        self.service.data_layers = [
            {"label": "Evenement", "code": 1, "icon_label": "event"}
        ]
        url = f"{settings.KINGSDAY_URL}1.json"

        responses.get(url, json=events.MOCK_DATA)
        self.service.get_full_data()

        self.assertEqual(self.service.data_url, settings.KINGSDAY_URL)

        # second call should still use the base url
        self.service.get_full_data()
        self.assertEqual(self.service.data_url, settings.KINGSDAY_URL)

    def test_get_custom_properties(self):
        mock_item = events.MOCK_DATA["features"][0]

        custom_properties = self.service.get_custom_properties(
            properties=mock_item["properties"],
            geom=mock_item["geometry"],
            layer_type="Evenement",
            icon_name="event",
        )

        self.assertEqual(custom_properties["aapp_subtitle"], "Evenement")

        # make sure lat and lon are correctly extracted from the geometry and added to the properties
        self.assertEqual(
            custom_properties["aapp_address"]["coordinates"]["lat"], 52.40028685
        )
        self.assertEqual(
            custom_properties["aapp_address"]["coordinates"]["lon"], 4.89489158
        )

    def test_first_aid_multipoint_geometry_is_converted_to_point(self):
        self.service.data_layers = [
            {"label": "EHBO", "code": 1, "icon_label": "first_aid"}
        ]
        url = f"{self.service.data_url}{self.service.data_layers[0]['code']}.json"

        responses.get(url, json=first_aid.MOCK_DATA)
        full_data = self.service.get_full_data()

        features = full_data["data"]["features"]

        # MultiPoint features should be converted to Point features (frontend expects a Point geometry)
        first = next(
            f for f in features if (f.get("properties") or {}).get("id") == "12619310"
        )
        self.assertEqual(first["geometry"]["type"], "Point")
        self.assertEqual(first["geometry"]["coordinates"], [4.899551, 52.377938])

        # Point features should remain unchanged
        another = next(
            f for f in features if (f.get("properties") or {}).get("id") == "12619313"
        )
        self.assertEqual(another["geometry"]["type"], "Point")
        self.assertEqual(another["geometry"]["coordinates"], [4.893404, 52.372925])
