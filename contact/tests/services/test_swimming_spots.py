import responses
from django.conf import settings

from contact.enums.swimming_spots import (
    SwimmingSpotFilter,
    SwimmingSpotIcons,
    SwimmingSpotProperties,
)
from contact.services.swimming_spots import SwimmingSpotService
from contact.tests.mock_data import swimming_spots
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class SwimmingSpotServiceTest(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.service = SwimmingSpotService()

    def test_get_full_data(self):
        responses.get(settings.PUBLIC_SWIMMING_SPOT_URL, json=swimming_spots.MOCK_DATA)

        full_data = self.service.get_full_data()

        self.assertEqual(full_data["filters"], SwimmingSpotFilter.choices_as_list())
        self.assertEqual(
            full_data["properties_to_include"], SwimmingSpotProperties.choices_as_list()
        )
        self.assertEqual(
            len(full_data["data"]["features"]),
            len(swimming_spots.MOCK_DATA["features"]),
        )
        self.assertEqual(
            full_data["icons_to_include"], SwimmingSpotIcons.choices_as_dict()
        )
        self.assertEqual(full_data["data"]["type"], "FeatureCollection")
