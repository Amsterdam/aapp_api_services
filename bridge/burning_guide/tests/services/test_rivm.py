from unittest.mock import patch

import pytest
import responses
from django.conf import settings
from requests.models import PreparedRequest

from bridge.burning_guide.serializers.advice import AdviceResponseSerializer
from bridge.burning_guide.services.rivm import RIVMService, UnknownPostalcodeError
from bridge.burning_guide.tests.mock_data import address_properties, postal_codes
from core.tests.test_authentication import ResponsesActivatedAPITestCase


class TestRIVMServiceNewRedStatus:
    @patch(
        "bridge.burning_guide.services.rivm.RIVMService.get_burning_guide_information"
    )
    @patch("bridge.burning_guide.services.rivm.RIVMService.get_bbox_from_postal_code")
    @pytest.mark.parametrize(
        "input_data,expected_result",
        [
            (
                {
                    "advice_0": 0,
                    "advice_6": 0,
                },
                False,
            ),
            (
                {
                    "advice_0": 2,
                    "advice_6": 2,
                },
                False,
            ),
            (
                {
                    "advice_0": 0,
                    "advice_6": 2,
                },
                True,
            ),
            (
                {
                    "advice_0": 2,
                    "advice_6": 0,
                },
                False,
            ),
        ],
    )
    def test_has_new_red_status(
        self,
        mock_get_bbox,
        mock_get_burning_guide_information,
        input_data,
        expected_result,
    ):
        postal_code = "1091"
        mock_get_bbox.return_value = {
            "min_x": 119329.2031,
            "min_y": 491975.6875,
            "max_x": 120966.2031,
            "max_y": 492166.9063,
        }
        response = AdviceResponseSerializer(
            data={
                "postal_code": postal_code,
                "model_runtime": "27-11-2025 10:00",
                "lki": 1,
                "wind": 6.8,
                "wind_bft": 4,
                "advice_0": input_data["advice_0"],
                "advice_6": input_data["advice_6"],
                "advice_12": 0,
                "advice_18": 0,
                "definitive_0": True,
                "definitive_6": True,
                "definitive_12": False,
                "definitive_18": False,
                "wind_direction": -1,
            }
        )
        response.is_valid(raise_exception=True)
        mock_get_burning_guide_information.return_value = response.validated_data

        rivm_service = RIVMService()
        has_new_red_status = rivm_service.has_new_red_status(postal_code=postal_code)
        assert has_new_red_status == expected_result


class TestRIVMService(ResponsesActivatedAPITestCase):
    def setUp(self):
        super().setUp()
        self.rivm_service = RIVMService()
        self.resp_postal_codes = responses.get(
            f"{settings.BURNING_GUIDE_AMSTERDAM_MAPS_URL}?KAARTLAAG=PC4_BUURTEN&THEMA=postcode",
            json=postal_codes.MOCK_RESPONSE,
        )

    def test_get_bbox_from_postal_code(self):
        bbox = self.rivm_service.get_bbox_from_postal_code(postal_code="1091")
        self.assertEqual(self.resp_postal_codes.call_count, 1)
        self.assertEqual(len(bbox.items()), 4)

    def test_get_bbox_from_postal_code_unknown(self):
        with self.assertRaises(UnknownPostalcodeError):
            self.rivm_service.get_bbox_from_postal_code(postal_code="1234")
        self.assertEqual(self.resp_postal_codes.call_count, 1)

    def test_get_burning_guide_information(self):
        postal_code = "1091"
        address_properties_url, bbox = self.create_url_address_properties(
            postal_code=postal_code
        )
        resp_address_prop = responses.get(
            address_properties_url, json=address_properties.MOCK_RESPONSE
        )

        validated_data = self.rivm_service.get_burning_guide_information(bbox=bbox)

        self.assertEqual(self.resp_postal_codes.call_count, 1)
        self.assertEqual(resp_address_prop.call_count, 1)
        self.assertEqual(type(validated_data), dict)
        self.assertEqual(validated_data["advice_0"], 0)
        self.assertEqual(validated_data["advice_6"], 0)
        self.assertEqual(validated_data["definitive_0"], True)
        self.assertEqual(validated_data["definitive_6"], True)

    def create_url_address_properties(self, postal_code: str):
        # get i and j value for address coordinates
        bbox = self.rivm_service.get_bbox_from_postal_code(postal_code=postal_code)
        payload = {
            "service": "WMS",
            "REQUEST": "GetFeatureInfo",
            "QUERY_LAYERS": "stookwijzer_v2",
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "FORMAT": "image/png",
            "TRANSPARENT": "true",
            "LAYERS": "stookwijzer_v2",
            "servicekey": self.rivm_service.service_key,
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

        formatted_url = self.build_url_with_params(
            f"{self.rivm_service.base_url}", payload
        )
        return formatted_url, bbox

    def build_url_with_params(self, url, params):
        req = PreparedRequest()
        req.prepare_url(url, params)
        return req.url
