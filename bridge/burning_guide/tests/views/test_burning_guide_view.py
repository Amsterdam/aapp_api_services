import responses
from django.conf import settings
from django.urls import reverse
from requests.models import PreparedRequest

from bridge.burning_guide.clients.rivm import RIVMClient
from bridge.burning_guide.tests.mock_data import address_properties, postal_codes
from core.tests.test_authentication import BasicAPITestCase

rivm_client = RIVMClient()


class BurningGuideView(BasicAPITestCase):
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

    @responses.activate
    def test_success(self):
        postal_code = "1091GW"

        resp_postal_codes = responses.get(
            f"{settings.BURNING_GUIDE_AMSTERDAM_MAPS_URL}?KAARTLAAG=PC4_BUURTEN&THEMA=postcode",
            json=postal_codes.MOCK_RESPONSE,
        )

        address_properties_url = create_url_address_properties(
            postal_code=postal_code[:4]
        )
        address_properties_resp = responses.get(
            address_properties_url, json=self.mock_address_properties_response
        )

        response = self.client.get(
            self.url + f"?postal_code={postal_code}",
            headers=self.api_headers,
        )

        self.assertEqual(address_properties_resp.call_count, 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp_postal_codes.call_count, 1)


def build_url_with_params(url, params):
    req = PreparedRequest()
    req.prepare_url(url, params)
    return req.url


def create_url_address_properties(postal_code: str):
    # get i and j value for address coordinates
    bbox = rivm_client.get_bbox_from_postal_code(postal_code=postal_code)

    payload = {
        "service": "WMS",
        "REQUEST": "GetFeatureInfo",
        "QUERY_LAYERS": "stookwijzer_v2",
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "FORMAT": "image/png",
        "TRANSPARENT": "true",
        "LAYERS": "stookwijzer_v2",
        "servicekey": rivm_client.service_key,
        "BUFFER": "1",
        "EXCEPTIONS": "INIMAGE",
        "info_format": "application/json",
        "feature_count": "1",
        "I": 128,
        "J": 128,
        "WIDTH": "256",
        "HEIGHT": "256",
        "CRS": "EPSG:28992",
        "BBOX": f"{bbox['min_x']},{bbox['min_y']},{bbox['max_x']},{bbox['max_y']}",
    }

    formatted_url = build_url_with_params(f"{rivm_client.base_url}", payload)

    return formatted_url
