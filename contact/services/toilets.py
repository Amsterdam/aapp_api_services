import logging
from urllib.parse import quote
import requests
from django.conf import settings
from django.core.cache import cache
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)

# Define filters for toilets
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

# List of properties to include in the response, this is also the order of which the properties will be shown in the frontend
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


class ToiletService:
    def __init__(self) -> None:
        self.url = settings.PUBLIC_TOILET_URL

    def get_full_data(self):

        toilets = self.get_toilets()

        full_toilet_data = []

        for toilet in toilets:
            new_properties = {}
            properties = toilet.get("properties", {})
            # add open hours to properties
            new_properties["open_hours"] = (
                f"{properties.get('Dagen_geopend', '')} {properties.get('Openingstijden', '')}"
            )
            if not new_properties["open_hours"].strip():
                new_properties["open_hours"] = None
            if properties.get("Foto"):
                # add image url to properties
                new_properties["image_url"] = (
                    f"{settings.PUBLIC_TOILET_IMAGE_BASE_URL}{quote(properties.get('Foto', ''))}"
                )
            else:
                new_properties["image_url"] = None
            new_properties["is_toilet"] = properties.get("SELECTIE", "").lower() in [
                "toegang",
                "openbaar",
                "parkeer",
            ]
            new_properties["price_per_use"] = properties.get("Prijs_per_gebruik", None)
            new_properties["name"] = properties.get("Soort", None)
            new_properties["description"] = properties.get("Omschrijving", None) or None
            new_properties["is_accessible"] = properties.get("SELECTIE", "").lower() == "toegang"

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
        cache_key = f"{__name__}.load_toilets"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        response = self._make_request()
        toilets = response.json().get("features", [])

        cache.set(cache_key, toilets, timeout=60 * 60 * 24)
        return toilets

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,  # Reraise the RequestException after retries
    )
    def _make_request(
        self,
    ) -> requests.Response:
        response = requests.get(url=self.url)
        response.raise_for_status()
        return response
