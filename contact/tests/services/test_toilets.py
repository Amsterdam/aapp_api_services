import responses
from django.conf import settings

from contact.enums.toilets import ToiletFilters, ToiletProperties
from contact.services.toilets import ToiletService
from contact.tests.mock_data import toilets
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class ToiletServiceTest(ResponsesActivatedAPITestCase):
    def setUp(self):
        self.service = ToiletService()

    def test_get_full_data(self):
        responses.get(settings.PUBLIC_TOILET_URL, json=toilets.MOCK_DATA)

        full_data = self.service.get_full_data()

        self.assertEqual(full_data["filters"], ToiletFilters.choices_as_list())
        self.assertEqual(
            full_data["properties_to_include"], ToiletProperties.choices_as_list()
        )
        self.assertEqual(
            len(full_data["data"]["features"]), len(toilets.MOCK_DATA["features"])
        )
        self.assertEqual(full_data["data"]["type"], "FeatureCollection")

    def test_construct_opening_hours_both(self):
        properties = {
            "Dagen_geopend": "ma - di - wo - do - vr - za - zo",
            "Openingstijden": "24 uur per dag",
        }
        opening_hours = self.service.construct_opening_hours(properties)
        self.assertEqual(
            opening_hours, "24 uur per dag\nma - di - wo - do - vr - za - zo"
        )

    def test_construct_opening_hours_only_days(self):
        properties = {
            "Dagen_geopend": "ma - di - wo - do - vr - za - zo",
            "Openingstijden": "",
        }
        opening_hours = self.service.construct_opening_hours(properties)
        self.assertEqual(opening_hours, "ma - di - wo - do - vr - za - zo")

    def test_construct_opening_hours_only_hours(self):
        properties = {
            "Dagen_geopend": "",
            "Openingstijden": "24 uur per dag",
        }
        opening_hours = self.service.construct_opening_hours(properties)
        self.assertEqual(opening_hours, "24 uur per dag")

    def test_construct_opening_hours_none(self):
        properties = {
            "Dagen_geopend": "",
            "Openingstijden": "",
        }
        opening_hours = self.service.construct_opening_hours(properties)
        self.assertEqual(opening_hours, None)
