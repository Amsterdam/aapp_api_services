import json

import requests
from django.conf import settings


class RIVMClient:
    def __init__(self) -> None:
        self.service_key = settings.BURNING_GUIDE_SERVICE_KEY
        self.base_url = settings.BURNING_GUIDE_RIVM_URL

    def get_burning_guide_information(self, bbox: dict[str, float]) -> dict:
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
        response_payload["postal_code"] = response_payload["pc4"]
        response_payload["advice_0"] = response_payload["advies_0"]
        response_payload["advice_6"] = response_payload["advies_6"]
        response_payload["advice_12"] = response_payload["advies_12"]
        response_payload["advice_18"] = response_payload["advies_18"]
        response_payload["definitive_0"] = response_payload["definitief_0"]
        response_payload["definitive_6"] = response_payload["definitief_6"]
        response_payload["definitive_12"] = response_payload["definitief_12"]
        response_payload["definitive_18"] = response_payload["definitief_18"]
        response_payload["wind_direction"] = response_payload["windrichting"]

        return response_payload
