import logging
from typing import Any, Dict
from urllib.parse import quote

from django.conf import settings

from contact.enums.toilets import ToiletFilters, ToiletProperties
from contact.services.service_abstract import ServiceAbstract

logger = logging.getLogger(__name__)


class ToiletService(ServiceAbstract):
    data_url = settings.PUBLIC_TOILET_URL

    def __init__(self) -> None:
        super().__init__()
        self.image_url = settings.PUBLIC_TOILET_IMAGE_BASE_URL

    def get_full_data(self) -> Dict[str, Any]:
        """
        Returns a dictionary containing:
        - filters: available filters for the frontend
        - properties_to_include: properties to include and their order
        - data: list of toilets with selected and custom properties
        """
        toilets = self.get_geojson_items()

        full_toilet_data = []

        for toilet in toilets:
            # get properties and add custom properties with prefix to avoid conflicts with original properties,
            properties = toilet.get("properties", {}) or {}
            custom_properties = self.get_custom_properties(properties)
            new_properties = {**properties, **custom_properties}

            # TODO: When out of MVP stage: implement a way to store all available properties in a database,
            # so that filters can be made on them and properties for the frontend can be selected.
            full_toilet_data.append(
                {
                    "id": toilet.get("id"),
                    "geometry": toilet.get("geometry"),
                    "properties": new_properties,
                }
            )

        full_data = {
            "filters": ToiletFilters.choices(),
            "properties_to_include": ToiletProperties.choices(),
            "data": full_toilet_data,
        }

        return full_data

    def get_custom_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a dictionary of custom properties for a toilet, using a prefix to avoid conflicts.
        """
        open_days = properties.get("Dagen_geopend", "")
        opening_times = properties.get("Openingstijden", "")
        open_hours = f"{open_days} {opening_times}".strip() or None

        picture = properties.get("Foto")
        image_url = f"{self.image_url}{quote(picture)}" if picture else None

        selectie = (properties.get("SELECTIE") or "").lower()
        return {
            f"{self.properties_prefix}open_hours": open_hours,
            f"{self.properties_prefix}description": properties.get("Omschrijving")
            or None,
            f"{self.properties_prefix}image_url": image_url,
            f"{self.properties_prefix}is_accessible": selectie == "toegang",
            f"{self.properties_prefix}is_toilet": selectie
            in ("toegang", "openbaar", "parkeer"),
        }
