from typing import Any, Dict

from contact.enums.kingsday_water import (
    LIST_PROPERTY,
    KingsdayWaterData,
    KingsdayWaterFilters,
    KingsdayWaterIcons,
    KingsdayWaterLayers,
    KingsdayWaterProperties,
)
from contact.services.kingsday_abstract import KingsdayAbstractService


class KingsdayWaterService(KingsdayAbstractService):
    data_enum = KingsdayWaterData
    filters_enum = KingsdayWaterFilters
    layers_enum = KingsdayWaterLayers
    properties_enum = KingsdayWaterProperties
    icons_enum = KingsdayWaterIcons
    list_property = LIST_PROPERTY

    def get_custom_properties(
        self,
        properties: Dict[str, Any],
        geom: Dict[str, Any],
        layer_type: str,
        icon_name: str | None,
    ) -> Dict[str, Any]:
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
        }
