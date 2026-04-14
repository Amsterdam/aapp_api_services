import responses
from django.conf import settings

from contact.enums.kingsday_land import (
    KingsdayLandFilters,
    KingsdayLandIcons,
    KingsdayLandProperties,
)
from contact.services.kingsday_land import KingsdayLandService
from contact.tests.mock_data.kingsday import events
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
        self.assertEqual(len(full_data["data"]["features"]), 2)

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

        # make sure lat an lon are correctly extracted from the geometry and added to the properties
        self.assertEqual(
            custom_properties["aapp_address"]["coordinates"]["lat"], 52.40028685
        )
        self.assertEqual(
            custom_properties["aapp_address"]["coordinates"]["lon"], 4.89489158
        )
