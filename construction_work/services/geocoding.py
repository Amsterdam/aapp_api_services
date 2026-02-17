import logging
import urllib.parse
from typing import Optional, Tuple

import requests
from django.conf import settings


def geocode_address(address: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Convert an address to latitude and longitude using the geocoding API.

    Args:
        address (str): The address to geocode.

    Returns:
        Tuple[Optional[float], Optional[float]]: A tuple containing latitude and longitude,
        or (None, None) if the geocoding fails.
    """
    try:
        encoded_address = urllib.parse.quote_plus(address)
        url = f"{settings.ADDRESS_TO_GPS_API}{encoded_address}"
        response = requests.get(url=url, timeout=1)
        response.raise_for_status()

        data = response.json()
        results = data.get("value", [])
        if not results:
            logging.warning(f"No results found for address: {address}")
            return None, None

        lon = results[0]["longitude"]
        lat = results[0]["latitude"]
        return lat, lon
    except requests.RequestException as e:
        logging.error(f"Error while geocoding address '{address}': {e}")
        return None, None
