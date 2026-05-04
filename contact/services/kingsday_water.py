from typing import Any, Dict

from contact.enums.kingsday_water import (
    LIST_PROPERTY,
    KingsdayWaterData,
    KingsdayWaterFilters,
    KingsdayWaterIcons,
    KingsdayWaterLayers,
    KingsdayWaterProperties,
    KingsdayWaterSilentProperties,
)
from contact.services.kingsday_abstract import KingsdayAbstractService


class KingsdayWaterService(KingsdayAbstractService):
    data_enum = KingsdayWaterData
    filters_enum = KingsdayWaterFilters
    layers_enum = KingsdayWaterLayers
    properties_enum = KingsdayWaterProperties
    silent_properties_enum = KingsdayWaterSilentProperties
    icons_enum = KingsdayWaterIcons
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
        However, the stroke and stroke-width properties for the 'Vaarrichting' layer are not prefixed,
        as they are used for styling the layer and the geojson standard is used.
        """
        if layer_type == "Vaarrichting" and geom.get("type") == "LineString":
            # for direction we want to add stroke and stroke-width properties
            stroke = "#FF9100"
            stroke_width = 5
        else:
            stroke = None
            stroke_width = None

        if layer_type in ["Afvalboot", "Vaarrichting"]:
            address = None
        else:
            address = self._get_address_from_properties(properties, geom)
        prefix = self.properties_prefix

        return {
            f"{prefix}title": properties.get("title", ""),
            f"{prefix}subtitle": layer_type,
            f"{prefix}icon_type": icon_name,
            f"{prefix}description": self._clean_html(properties.get("description"))
            or None,
            f"{prefix}website": properties.get("website") or None,
            f"{prefix}address": address,
            "stroke": stroke,
            "stroke-width": stroke_width,
        }
