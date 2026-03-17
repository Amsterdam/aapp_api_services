import responses
from django.conf import settings

from contact.enums.taps import TapFilters, TapProperties
from contact.services.taps import TapService
from contact.tests.mock_data import taps
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class TapServiceTest(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.service = TapService()

    def test_get_full_data(self):

        responses.get(settings.TAP_URL, json=taps.MOCK_DATA)
        full_data = self.service.get_full_data()
        self.assertEqual(full_data["filters"], TapFilters.choices())
        self.assertEqual(full_data["properties_to_include"], TapProperties.choices())
        self.assertEqual(len(full_data["data"]["features"]), 3)

    def test_filter_data(self):
        # Test that filter_data correctly filters taps based on the provided filters
        taps_data = taps.MOCK_DATA["features"]

        # Filter for drinking taps
        filtered_taps = self.service.filter_data(taps_data)
        self.assertEqual(len(filtered_taps), 3)
        self.assertTrue(
            all(
                tap["properties"]["plaats"] in ["Amsterdam", "Weesp", "Amsterdamse bos"]
                for tap in filtered_taps
            )
        )

    def test_get_geometry_from_properties(self):
        properties = taps.MOCK_DATA["features"][0]["properties"]
        geometry = self.service.get_geometry_from_properties(properties)
        self.assertEqual(geometry["coordinates"][0], properties["longitude"])
        self.assertEqual(geometry["coordinates"][1], properties["latitude"])

    def test_get_geometry_from_properties_missing_coordinates(self):
        properties = {}
        geometry = self.service.get_geometry_from_properties(properties)
        self.assertEqual(geometry, {})

    def test_get_custom_properties_24_7_open(self):
        properties = {
            "beschrijvi": "Watertap vlak bij pont.",
            "type": "Regulier, 24-7 open",
        }
        custom_properties = self.service.get_custom_properties(properties)
        self.assertEqual(custom_properties["aapp_title"], "Watertap")
        self.assertEqual(custom_properties["aapp_has_malfunction"], False)
        self.assertEqual(custom_properties["aapp_type"], "24 uur per dag beschikbaar")

    def test_get_custom_properties_has_malfunction(self):
        properties = {
            "beschrijvi": "Fontein bij het park.",
            "type": "Storing",
        }
        custom_properties = self.service.get_custom_properties(properties)
        self.assertEqual(custom_properties["aapp_title"], "Drinkfontein")
        self.assertEqual(custom_properties["aapp_has_malfunction"], True)
        self.assertEqual(custom_properties["aapp_type"], None)
