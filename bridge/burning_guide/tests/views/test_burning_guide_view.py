import json

import responses
from django.urls import reverse
from requests.models import PreparedRequest

from bridge.burning_guide.clients.geodan import GeoDanClient
from bridge.burning_guide.clients.rivm import RIVMClient
from bridge.burning_guide.tests.mock_data import (
    address_coordinates,
    address_id,
    address_properties,
)
from bridge.burning_guide.utils import calculate_bbox_from_wsg_coordinates
from core.tests.test_authentication import BasicAPITestCase

geodan_client = GeoDanClient()
rivm_client = RIVMClient()


class BurningGuideView(BasicAPITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("burning-guide")
        self.mock_address_id_response = json.dumps(address_id.MOCK_RESPONSE).encode(
            "utf-8"
        )
        self.mock_address_coordinates_response = json.dumps(
            address_coordinates.MOCK_RESPONSE
        ).encode("utf-8")
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
        postal_code = "1011AB"

        address_id_url = create_url_address_id(postal_code)

        address_id_resp = responses.get(
            address_id_url, body=self.mock_address_id_response
        )

        address_id = geodan_client._get_address_id_from_response_data(
            address_id_resp.body
        )

        address_coordinates_url = create_url_address_coordinates(address_id)
        address_coordinates_resp = responses.get(
            address_coordinates_url, body=self.mock_address_coordinates_response
        )

        address_coordinates = geodan_client._get_coordinates_from_response_data(
            address_coordinates_resp.body
        )

        address_properties_url = create_url_address_properties(
            address_coordinates[0], address_coordinates[1]
        )
        address_properties_resp = responses.get(
            address_properties_url, json=self.mock_address_properties_response
        )

        response = self.client.get(
            self.url + f"?postal_code={postal_code}",
            headers=self.api_headers,
        )

        self.assertEqual(address_id_resp.call_count, 1)
        self.assertEqual(address_coordinates_resp.call_count, 1)
        self.assertEqual(address_properties_resp.call_count, 1)
        self.assertEqual(response.status_code, 200)


def build_url_with_params(url, params):
    req = PreparedRequest()
    req.prepare_url(url, params)
    print(req.url)
    return req.url


def create_url_address_id(postal_code):
    payload = {
        "servicekey": geodan_client.service_key,
        "country": "NLD",
        "type": "address",
        "query": postal_code,
    }
    formatted_url = build_url_with_params(f"{geodan_client.base_url}/suggest", payload)
    return formatted_url


def create_url_address_coordinates(address_id):
    payload = {"servicekey": geodan_client.service_key, "id": address_id}
    formatted_url = build_url_with_params(f"{geodan_client.base_url}/lookup", payload)
    return formatted_url


def create_url_address_properties(address_lon, address_lat):
    # get i and j value for address coordinates
    bbox = calculate_bbox_from_wsg_coordinates(address_lon, address_lat)

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
