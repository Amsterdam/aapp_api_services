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

        self.assertEqual(full_data["filters"], ToiletFilters.choices())
        self.assertEqual(full_data["properties_to_include"], ToiletProperties.choices())
        self.assertEqual(len(full_data["data"]), len(toilets.MOCK_DATA["features"]))
