from typing import Any, Dict

from django.conf import settings

from contact.enums.swimming_spots import (
    LIST_PROPERTY,
    SwimmingSpotFilter,
    SwimmingSpotIcons,
    SwimmingSpotLayers,
    SwimmingSpotProperties,
)
from contact.services.service_abstract import ServiceAbstract

SUBTITLE_ICON_MAPPING = {
    "Binnenzwembad": "indoor_pool",
    "Buitenzwembad": "outdoor_pool",
    "Officiële buitenzwemplek": "outdoor_spot",
    "Peuterbadje": "kids_pool",
    "Waterspeeltuin": "water_park",
}


class SwimmingSpotService(ServiceAbstract):
    data_url = settings.PUBLIC_SWIMMING_SPOT_URL

    def __init__(self) -> None:
        super().__init__()

    def get_full_data(self) -> Dict[str, Any]:
        """
        Returns a dictionary containing:
        - filters: available filters for the frontend
        - properties_to_include: properties to include and their order
        - data: list of swimming spots with selected and custom properties
        """
        swimming_spots = self.get_geojson_items()

        full_swimming_spot_data = []

        for swimming_spot in swimming_spots:
            # get properties and add custom properties with prefix to avoid conflicts with original properties,
            properties = swimming_spot.get("properties", {}) or {}
            custom_properties = self.get_custom_properties(properties)
            new_properties = {**properties, **custom_properties}

            # TODO: When out of MVP stage: implement a way to store all available properties in a database,
            # so that filters can be made on them and properties for the frontend can be selected.
            full_swimming_spot_data.append(
                {
                    "id": swimming_spot.get("id"),
                    "type": swimming_spot.get("type"),
                    "geometry": swimming_spot.get("geometry"),
                    "properties": new_properties,
                }
            )

        full_data = self.build_response_payload(
            items=full_swimming_spot_data,
            filters=SwimmingSpotFilter,
            layers=SwimmingSpotLayers,
            properties_to_include=SwimmingSpotProperties,
            icons=SwimmingSpotIcons,
            list_property=LIST_PROPERTY,
        )

        return full_data

    def get_custom_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a dictionary of custom properties for a swimming spot, using a prefix to avoid conflicts.

        Note: aapp_title should ALWAYS be included as a custom property, as it is used as the main title for the swimming spot in the frontend.
        """
        # for subtitle, we want to use the "Categorie" property, but map "Zwemplek" to "Officiële buitenzwemplek" for the subtitle, and use the icon mapping for the icon type.
        subtitle = properties.get("Categorie", "")
        if subtitle == "Zwemplek":
            subtitle = "Officiële buitenzwemplek"

        return {
            f"{self.properties_prefix}title": properties.get("Naam_locatie", "")
            or "Zwemplek",
            f"{self.properties_prefix}subtitle": subtitle,
            f"{self.properties_prefix}icon_type": SUBTITLE_ICON_MAPPING.get(
                subtitle, SwimmingSpotIcons.INDOOR_POOL.value.label
            ),
        }
