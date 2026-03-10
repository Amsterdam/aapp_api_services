import logging
import re
from typing import Any, Dict

import requests
from django.conf import settings
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from core.utils.caching_utils import cache_instance_independent_function

logger = logging.getLogger(__name__)


class FetchError(Exception):
    pass


class AddressService:
    def __init__(self) -> None:
        self.url = settings.ADDRESS_SEARCH_URL

    @cache_instance_independent_function(
        timeout=60 * 60 * 24 * 28
    )  # Cache the result for 4 weeks
    def get_address_by_coordinates(
        self, latitude: float, longitude: float
    ) -> Dict[str, Any] | None:
        params = self.construct_params(latitude=latitude, longitude=longitude)
        response = self.make_request(params=params)
        try:
            data = response.json()
        except ValueError as e:
            raise FetchError(
                f"Invalid JSON response for coordinates ({latitude}, {longitude})"
            ) from e

        try:
            response_data = data.get("response")
        except AttributeError:
            logger.error(f"Invalid response format: {data}")
            return None

        if not response_data:
            logger.error(f"Invalid response: {data}")
            return None

        if not response_data.get("docs"):
            return None

        return self._rename_fields_for_serializer(data=response_data["docs"][0])

    def construct_params(
        self, latitude: float, longitude: float
    ) -> list[tuple[str, str]]:
        params = [
            (
                "fl",
                "straatnaam huisnummer huisletter huisnummertoevoeging postcode woonplaatsnaam type nummeraanduiding_id centroide_ll",
            ),
            (
                "qf",
                "exacte_match^1 suggest^0.5 straatnaam^0.6 huisnummer^0.5 huisletter^0.5 huisnummertoevoeging^0.5",
            ),
            ("fq", "bron:BAG"),
            ("bq", "type:weg^1.5"),
            ("bq", "type:adres^1"),
            ("lat", latitude),
            ("lon", longitude),
            ("fq", "type:adres"),
            ("rows", "1"),
        ]
        return params

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(FetchError),
        reraise=True,  # Reraise the FetchError after retries
    )
    def make_request(self, params: list[tuple[str, str]]) -> requests.Response:
        try:
            response = requests.get(
                self.url,
                params=params,
                headers={"Referer": "app.amsterdam.nl"},
                timeout=5,
            )
            response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to Mijn Amsterdam API failed: {e}")
            raise FetchError()
        return response

    def _rename_fields_for_serializer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # get lat and long from coordinates
        coordinates = self._get_lat_and_lon_from_coordinates(data["centroide_ll"])
        # change naming of fields
        data["city"] = data["woonplaatsnaam"]
        data["street"] = data["straatnaam"]
        data["lat"] = coordinates[0]
        data["lon"] = coordinates[1]
        data["number"] = data.get("huisnummer", "")
        data["bagId"] = data.get("nummeraanduiding_id", "")

        if data.get("huisletter") is not None and data.get("huisletter") != "":
            data["additionLetter"] = data.get("huisletter")
        if (
            data.get("huisnummertoevoeging") is not None
            and data.get("huisnummertoevoeging") != ""
        ):
            data["additionNumber"] = data.get("huisnummertoevoeging")

        return data

    @staticmethod
    def _get_lat_and_lon_from_coordinates(coordinates: str) -> tuple[float, float]:
        if hasattr(coordinates, "coords"):
            lon, lat = coordinates.coords
            return lat, lon
        m = re.match(r"POINT\(\s*([-0-9.]+)\s+([-0-9.]+)\s*\)", coordinates)
        if not m:
            return None, None
        lon, lat = m.groups()
        return float(lat), float(lon)
