import responses
from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from freezegun import freeze_time

from core.tests.test_authentication import BasicAPITestCase
from waste.tests import data


class TestWasteCalendarView(BasicAPITestCase):
    @freeze_time("2024-04-01")
    @override_settings(CALENDAR_LENGTH=14)
    @responses.activate
    def test_calendar_simple_success(self):
        # Mock the response from the external API
        responses.get(settings.WASTE_GUIDE_URL, json=data.AFVALWIJZER_DATA_MINIMAL)

        url = reverse("waste-guide-calendar")
        response = self.client.get(
            url,
            data={"bag_nummeraanduiding_id": "12345"},
            headers=self.api_headers,
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()

        expected_calendar = [
            {
                "date": f"2024-04-{day}",
                "label": "Groente, Fruit en Tuin Afval",
                "code": "GFT",
                "curb_rules_from": None,
                "curb_rules_to": None,
                "alert": "Breng uw kerstboom naar een <a "
                "href=http://amsterdam.nl/recyclepunten>Recyclepunt.  </a>",
            }
            for day in ["01", "02", "03", "08", "09", "10"]
        ]
        self.assertEqual(result["calendar"], expected_calendar)
        for waste_type in result["waste_types"]:
            if waste_type["code"] == "GFT":
                self.assertEqual(waste_type["next_date"], "2024-04-01")
