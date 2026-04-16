from typing import Any, Dict, List

from contact.enums.kingsday_land import (
    LIST_PROPERTY,
    KingsdayLandData,
    KingsdayLandFilters,
    KingsdayLandIcons,
    KingsdayLandLayers,
    KingsdayLandProperties,
    KingsdayLandSilentProperties,
)
from contact.services.kingsday_abstract import KingsdayAbstractService


class KingsdayLandService(KingsdayAbstractService):
    data_enum = KingsdayLandData
    filters_enum = KingsdayLandFilters
    layers_enum = KingsdayLandLayers
    properties_enum = KingsdayLandProperties
    silent_properties_enum = KingsdayLandSilentProperties
    icons_enum = KingsdayLandIcons
    list_property = LIST_PROPERTY

    def get_custom_properties(
        self,
        properties: Dict[str, Any],
        geom: Dict[str, Any],
        layer_type: str,
        icon_name: str | None,
    ) -> Dict[str, Any]:
        """
        Returns a dictionary of custom properties for a given data point,
        based on the original properties, geometry, layer type, and icon name.

        All custom properties are prefixed with 'aapp_' to avoid conflicts with original properties.
        However, the fill and fill_opacity properties for the 'Omleiding' layer are not prefixed,
        as they are used for styling the layer and the geojson standard is used.
        """
        address = self._get_address_from_properties(properties, geom)
        prefix = self.properties_prefix

        if layer_type == "Omleiding" and geom.get("type") == "Polygon":
            # for detour we want to add fill and opacity properties
            fill = "#EC0000"
            fill_opacity = 0.2
        else:
            fill = None
            fill_opacity = None

        return {
            f"{prefix}title": properties.get("title", ""),
            f"{prefix}subtitle": layer_type,
            f"{prefix}icon_type": icon_name,
            f"{prefix}description": self._clean_html(properties.get("description"))
            or None,
            f"{prefix}website": properties.get("website") or None,
            f"{prefix}address": address,
            f"{prefix}toilet_table": self._create_toilet_table(
                properties.get("meta", [])
            ),
            "fill": fill,
            "fill-opacity": fill_opacity,
        }

    def _create_toilet_table(
        self, meta: List[Dict[str, str]]
    ) -> List[Dict[str, str]] | None:
        """
        Converts the 'meta' field from the original data into a structured format for the 'aapp_toilet_table' property.
        """
        if not meta:
            return None

        table = []
        for item in meta:
            key = item.get("title")
            value = item.get("value")
            if key and value:
                table.append({"key": key, "value": value})

        return table
