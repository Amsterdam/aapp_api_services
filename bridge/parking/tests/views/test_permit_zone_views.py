from unittest.mock import patch

from django.urls import reverse

from core.tests.test_authentication import BasicAPITestCase


class TestPermitZoneView(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("parking-permit-zones")

    @patch("bridge.parking.views.permit_zone_views.requests.get")
    def test_get_permit_zone_successfully(self, mock_request_get):
        mock_request_get.return_value.status_code = 200
        mock_request_get.return_value.json.return_value = {
            "data": {
                "calculatedGeometry": '{"type": "FeatureCollection", "features": []}'
            }
        }
        response = self.client.get(
            self.url, {"permit_zone": "test"}, headers=self.api_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["type"], "FeatureCollection")
        self.assertEqual(response.data["features"], [])
