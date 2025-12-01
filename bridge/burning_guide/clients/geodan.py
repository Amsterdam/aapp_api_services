import json

import requests
from django.conf import settings


class GeoDanClient:
    def __init__(self) -> None:
        self.service_key = settings.BURNING_GUIDE_SERVICE_KEY
        self.base_url = settings.BURNING_GUIDE_GEODAN_URL

    def get_address_id(self, postal_code) -> str:
        # define payload
        payload = {
            "servicekey": self.service_key,
            "country": "NLD",
            "type": "address",
            "query": postal_code,
        }

        # make request to get address id
        address_id_response = requests.get(f"{self.base_url}/suggest", params=payload)
        # convert response to json
        address_id_response.raise_for_status()

        address_id = self._get_address_id_from_response_data(
            address_id_response.content
        )

        return address_id

    def get_address_coordinates(self, address_id) -> list[float]:
        payload = {"servicekey": self.service_key, "id": address_id}

        address_coordinates_response = requests.get(
            f"{self.base_url}/lookup", params=payload
        )
        # address_coordinates_data = ADDRESS_COORDINATES_RESPONSE
        address_coordinates_response.raise_for_status()

        address_coordinates = self._get_coordinates_from_response_data(
            address_coordinates_response.content
        )

        return address_coordinates

    def _get_address_id_from_response_data(self, response_data) -> str:
        address_id_response_data_json = json.loads(response_data.decode("utf-8"))

        # get address id from response
        address_id = address_id_response_data_json["features"][0]["id"]

        return address_id

    def _get_coordinates_from_response_data(self, response_data) -> list[float]:
        address_coordinates_response_data_json = json.loads(
            response_data.decode("utf-8")
        )

        # get coordinates from data
        address_coordinates = address_coordinates_response_data_json["features"][0][
            "centroid"
        ]["coordinates"]

        return address_coordinates
