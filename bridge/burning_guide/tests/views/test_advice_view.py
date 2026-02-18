from unittest.mock import patch

from django.urls import reverse

from bridge.burning_guide.tests.mock_data import address_properties
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class BurningGuideView(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("burning-guide")
        self.mock_address_properties_response = address_properties.MOCK_RESPONSE

    def test_postal_code_invalid(self):
        postal_code = "not_valid"
        response = self.client.get(
            self.url + f"?postal_code={postal_code}", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 400)

    def test_postal_code_outside_amsterdam(self):
        postal_code = "1234AB"
        response = self.client.get(
            self.url + f"?postal_code={postal_code}", headers=self.api_headers
        )
        self.assertEqual(response.status_code, 400)

    @patch("bridge.burning_guide.views.advice_view.rivm_client")
    def test_success(self, patched_rivm_service):
        patched_rivm_service.get_bbox_from_postal_code.return_value = {
            "min_x": 121000,
            "min_y": 487000,
            "max_x": 122000,
            "max_y": 488000,
        }
        patched_rivm_service.get_burning_guide_information.return_value = {
            "validated": "data"
        }

        postal_code = "1091"
        response = self.client.get(
            self.url + f"?postal_code={postal_code}",
            headers=self.api_headers,
        )
        self.assertEqual(response.status_code, 200)

    @patch("bridge.burning_guide.views.advice_view.rivm_client")
    def test_success_full_postal_code(self, patched_rivm_service):
        patched_rivm_service.get_bbox_from_postal_code.return_value = {
            "min_x": 121000,
            "min_y": 487000,
            "max_x": 122000,
            "max_y": 488000,
        }
        patched_rivm_service.get_burning_guide_information.return_value = {
            "validated": "data"
        }

        postal_code = "1091BX"
        response = self.client.get(
            self.url + f"?postal_code={postal_code}",
            headers=self.api_headers,
        )
        self.assertEqual(response.status_code, 200)
