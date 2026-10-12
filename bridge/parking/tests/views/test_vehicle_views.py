import responses
from django.urls import reverse

from core.tests.test_authentication import ResponsesActivatedAPITestCase


class TestVehicleInformationView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-vehicle-information")

    def test_licence_plate_not_found(self):
        licence_plate = "not_valid"

        responses.get(
            "https://opendata.rdw.nl/resource/m9d7-ebf2.json",
            json=[],
            status=200,
        )
        response = self.client.get(
            self.url + f"?licence_plate={licence_plate}", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": False, "content": None})

    def test_licence_plate_found(self):
        licence_plate = "valid_plate"
        mock_response = [
            {
                "merk": "Toyota",
                "handelsbenaming": "Corolla",
                "eerste_kleur": "Rood",
            }
        ]
        responses.get(
            "https://opendata.rdw.nl/resource/m9d7-ebf2.json",
            json=mock_response,
            status=200,
        )
        response = self.client.get(
            self.url + f"?licence_plate={licence_plate}", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "success": True,
                "content": {
                    "brand": "Toyota",
                    "type": "Corolla",
                    "color": "Rood",
                },
            },
        )
