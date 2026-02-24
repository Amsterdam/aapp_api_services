import logging
from typing import Any, Dict
from urllib.parse import quote

import requests
from django.conf import settings
from django.core.cache import cache
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)

TOILET_FILTERS = [
    {
        "label": "Gratis",
        "filter_key": "price_per_use",
        "filter_value": 0,
    },
    {
        "label": "Rolstoeltoegankelijk",
        "filter_key": "is_accessible",
        "filter_value": True,
    },
    {
        "label": "Toilet",
        "filter_key": "is_toilet",
        "filter_value": True,
    },
]

PROPERTIES_TO_INCLUDE = [
    {
        "label": "Titel",
        "property_key": "name",
        "property_type": "string",
        "icon": None,
    },
    {
        "label": "Openingstijden",
        "property_key": "open_hours",
        "property_type": "string",
        "icon": "toilet",
    },
    {
        "label": "Prijs",
        "property_key": "price_per_use",
        "property_type": "float",
        "icon": "toilet",
    },
    {
        "label": "Omschrijving",
        "property_key": "description",
        "property_type": "string",
        "icon": "toilet",
    },
    {
        "label": "Afbeelding",
        "property_key": "image_url",
        "property_type": "url",
        "icon": None,
    },
]

# Cache and timeout for toilet data, since the data is not expected to change frequently and the request can be slow, we cache it for 24 hours
CACHE_TIMEOUT = 60 * 60 * 24


class ToiletService:
    def __init__(self) -> None:
        self.url = settings.PUBLIC_TOILET_URL
        self._cache_key = f"{__name__}.load_toilets"

    def get_full_data(self) -> Dict[str, Any]:
        """Return toilets formatted with the selected properties and metadata.
        The response includes:
        - filters: the available filters for the frontend
        - properties_to_include: the properties to include in the response, this is also the order of which the properties will be shown in the frontend
        - data: the list of toilets with the selected properties and metadata
        """
        toilets = self.get_toilets()

        full_toilet_data = []

        for toilet in toilets:
            properties = toilet.get("properties", {}) or {}

            selection = str(properties.get("SELECTIE", "")).lower()

            # Build open hours from available parts, normalize empty string to None
            open_days = properties.get("Dagen_geopend") or ""
            opening_times = properties.get("Openingstijden") or ""
            open_hours = (
                " ".join(part for part in (open_days, opening_times) if part).strip()
                or None
            )

            foto = properties.get("Foto")
            if foto:
                image_url = f"{settings.PUBLIC_TOILET_IMAGE_BASE_URL}{quote(foto)}"
            else:
                image_url = None

            new_properties = {
                "name": properties.get("Soort"),
                "open_hours": open_hours,
                "price_per_use": properties.get("Prijs_per_gebruik"),
                "description": properties.get("Omschrijving") or None,
                "image_url": image_url,
                "is_accessible": selection == "toegang",
                "is_toilet": selection in ("toegang", "openbaar", "parkeer"),
            }

            full_toilet_data.append(
                {
                    "id": toilet.get("id"),
                    "geometry": toilet.get("geometry"),
                    "properties": new_properties,
                }
            )

        full_data = {
            "filters": TOILET_FILTERS,
            "properties_to_include": PROPERTIES_TO_INCLUDE,
            "data": full_toilet_data,
        }

        return full_data

    def get_toilets(self):
        cached_data = cache.get(self._cache_key)
        if cached_data:
            return cached_data

        try:
            response = self._make_request()
        except requests.exceptions.RequestException:
            raise

        toilets = response.json().get("features", []) if response is not None else []

        cache.set(self._cache_key, toilets, timeout=CACHE_TIMEOUT)
        return toilets

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,  # Reraise the RequestException after retries
    )
    def _make_request(self) -> requests.Response:
        """Make the HTTP request for toilet data with retries and a timeout."""
        try:
            response = requests.get(url=self.url)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            logger.info("Failed to fetch public toilet data")
            raise
