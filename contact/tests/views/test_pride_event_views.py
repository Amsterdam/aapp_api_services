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

    def test_lolas_huis_keeps_meta_dates_and_raw_multiline_time(self):
        responses.get(settings.PRIDE_EVENT_URL, json=events.MOCK_DATA)

        url = reverse("contact-pride-events")
        response = self.client.get(url, headers=self.api_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        event = next(item for item in response.json() if item["id"] == "13073997")

        self.assertEqual(event["title"], "Lola's Huis")
        self.assertEqual(event["date_start"], "2026-07-17")
        self.assertEqual(event["date_end"], "2026-07-18")
        self.assertEqual(
            event["time"],
            "16-07-2026 - 20:30\n17-07-2026 - 20:30\n17-07-2026 - 22:30\n18-07-2026 - 20:30",
        )
