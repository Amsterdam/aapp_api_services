import responses
from django.conf import settings
from django.urls import reverse
from rest_framework import status

from contact.tests.mock_data.pride import events
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class TestPrideEventView(ResponsesActivatedAPITestCase):
    def test_success(self):
        responses.get(settings.PRIDE_EVENT_URL, json=events.MOCK_DATA)

        url = reverse("contact-pride-events")
        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
