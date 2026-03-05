import logging
import re
import json
from typing import Any, Dict
from django.conf import settings
import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)

from core.utils.caching_utils import cache_function


class AddressService:

    def __init__(self) -> None:
        self.url = settings.ADDRESS_SEARCH_URL

    @cache_function(timeout=60 * 60 * 24 * 7)  # Cache the result for 1 week
    def get_address_by_coordinates(self, latitude: float, longitude: float) -> Dict[str, Any]:
        response = self._make_request(latitude, longitude)

        data = json.loads(response.content)
        if not data.get("response"):
            logger.error(f"Invalid response: {data}")
            raise ValueError("Invalid response from address search API")
        
        response_data = self._rename_fields_for_serializer(data=data["response"]["docs"][0]) if data["response"]["docs"] else None
        
        return response_data
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,  # Reraise the RequestException after retries
    )
    def _make_request(self, latitude: float, longitude: float) -> requests.Response:
        """Make the HTTP request for toilet data with retries and a timeout."""

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
        ]
        params.append(("lat", latitude))
        params.append(("lon", longitude))

        params.append(("fq", "type:adres"))
        params.append(("rows", "1"))
        try:
            response = requests.get(
                settings.ADDRESS_SEARCH_URL,
                params=params,
                headers={"Referer": "app.amsterdam.nl"},
                timeout=5,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            logger.info("Failed to fetch data", extra={"url": self.data_url})
            raise

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
        if data.get("huisnummertoevoeging") is not None and data.get("huisnummertoevoeging") != "":
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