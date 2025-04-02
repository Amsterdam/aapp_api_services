from unittest.mock import Mock, patch

from django.test import override_settings
from django.urls import reverse
from freezegun import freeze_time

from core.tests.test_authentication import BasicAPITestCase
from waste.tests import data


class TestWasteCalendarView(BasicAPITestCase):
    @freeze_time("2024-04-01")
    @override_settings(CALENDAR_LENGTH=14)
    @patch("requests.get")
    def test_calendar_simple_success(self, mock_request):
        # Mock the response from the external API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = data.AFVALWIJZER_DATA_MINIMAL
        mock_request.return_value = mock_response

        url = reverse("waste-guide-calendar")
        response = self.client.get(
            url,
            data={"bag_nummeraanduiding_id": "12345"},
            headers=self.api_headers,
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        mock_request.assert_called_once()

        expected_calendar = [
            {
                "date": f"2024-04-{day}",
                "label": "Groente, Fruit en Tuin Afval",
                "type": "GFT",
                "curb_rules_from": None,
                "curb_rules_to": None,
                "note": "Breng uw kerstboom naar een <a "
                "href=http://amsterdam.nl/recyclepunten>Recyclepunt.  </a>",
            }
            for day in ["01", "02", "03", "08", "09", "10"]
        ]
        self.assertEqual(result["calendar"], expected_calendar)
        for waste_type in result["waste_types"]:
            if waste_type["type"] == "GFT":
                self.assertEqual(waste_type["next_date"], "2024-04-01")
