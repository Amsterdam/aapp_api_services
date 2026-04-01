import responses
from django.conf import settings
from django.urls import reverse

from bridge.boat_charging.tests.mock_data import locations
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class TestBurningGuideNotificationCreateView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("boat-charging-locations")

    def test_success(self):
        resp = responses.get(
            settings.BOAT_CHARGING_ENDPOINTS["LOCATIONS"],
            status=200,
            json=locations.MOCK_RESPONSE,
        )
        response = self.client.post(self.url, headers=self.api_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp.call_count, 1)
