import json

import requests
import shapely
from django.conf import settings
from django.core.cache import cache

from bridge.burning_guide.serializers.advice import AdviceResponseSerializer
from bridge.burning_guide.utils import calculate_rd_bbox_from_wsg_coordinates


def load_postal_data():
    """
    Function to load the postal data:
    - make request to amsterdam maps data
    - for each postal code:
        - calculate midpoint (this is in wsg)
        - transform to rijksdriehoek
        - calculate bbox
        - save to dict
    """
    cache_key = f"{__name__}.load_postal_data"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    url = settings.BURNING_GUIDE_AMSTERDAM_MAPS_URL
    params = {"KAARTLAAG": "PC4_BUURTEN", "THEMA": "postcode"}
    response = requests.get(url, params=params)

    response.raise_for_status()
    data_json = response.json()
    postal_codes_raw = data_json["features"]

    final_dict = {}
    for postal_code_features in postal_codes_raw:
        # get postal code and geometry
        postal_code = postal_code_features["properties"]["Postcode4"]
        polygon_object = shapely.geometry.shape(postal_code_features["geometry"])

        # calculate centroid
        centroid_object = polygon_object.centroid

        # calculate bbox in rijksdriehoek coordinates
        bbox = calculate_rd_bbox_from_wsg_coordinates(
            lon=centroid_object.x, lat=centroid_object.y
        )

        # add bbox to final dict
        final_dict[postal_code] = bbox

    cache.set(cache_key, final_dict, timeout=60 * 60 * 24)
    return final_dict


class RIVMService:
    def __init__(self) -> None:
        self.service_key = settings.BURNING_GUIDE_SERVICE_KEY
        self.base_url = settings.BURNING_GUIDE_RIVM_URL
        self.model_runtime = None

    def has_new_red_status(self, postal_code):
        bbox = self.get_bbox_from_postal_code(postal_code)
        data = self.get_burning_guide_information(bbox=bbox)

        if data["advice_0"] == 2 or not data["definitive_0"]:
            # current status is already red or not definitive
            return False
        elif data["advice_6"] == 2 and data["definitive_6"]:
            # new red status in 6 hours
            return True
        else:
            return False

    def get_burning_guide_information(
        self, bbox: dict[str, float]
    ) -> AdviceResponseSerializer:
        payload = {
            "service": "WMS",
            "REQUEST": "GetFeatureInfo",
            "QUERY_LAYERS": "stookwijzer_v2",
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "FORMAT": "image/png",
            "TRANSPARENT": "true",
            "LAYERS": "stookwijzer_v2",
            "servicekey": self.service_key,
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

        # get information from request
        response = requests.get(f"{self.base_url}", params=payload)
        response.raise_for_status()
        data = response.content
        json_data = json.loads(data.decode("utf-8"))

        # only extract properties from response
        response_payload = json_data["features"][0]["properties"]

        # change naming of fields
        response_payload["postal_code"] = response_payload["pc4"][:4]  # first 4 digits
        response_payload["advice_0"] = response_payload["advies_0"]
        response_payload["advice_6"] = response_payload["advies_6"]
        response_payload["advice_12"] = response_payload["advies_12"]
        response_payload["advice_18"] = response_payload["advies_18"]
        response_payload["definitive_0"] = response_payload["definitief_0"]
        response_payload["definitive_6"] = response_payload["definitief_6"]
        response_payload["definitive_12"] = response_payload["definitief_12"]
        response_payload["definitive_18"] = response_payload["definitief_18"]
        response_payload["wind_direction"] = response_payload["windrichting"]

        request_serializer = AdviceResponseSerializer(data=response_payload)
        request_serializer.is_valid(raise_exception=True)
        return request_serializer.validated_data

    def get_bbox_from_postal_code(self, postal_code: str) -> dict:
        data = load_postal_data()
        # only use the first 4 characters of the postal code
        bbox = data.get(postal_code)
        if not bbox:
            raise ValueError("Unknown postal code")
        return bbox
