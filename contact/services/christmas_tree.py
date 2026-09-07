from typing import Any, Dict

from contact.enums.christmas_tree import (
    LIST_PROPERTY,
    ChristmasTreeData,
    ChristmasTreeFilters,
    ChristmasTreeIcons,
    ChristmasTreeLayers,
    ChristmasTreeProperties,
    ChristmasTreeSilentProperties,
)
from contact.services.event_abstract import EventAbstractService


class ChristmasTreeService(EventAbstractService):
    data_enum = ChristmasTreeData
    filters_enum = ChristmasTreeFilters
    layers_enum = ChristmasTreeLayers
    properties_enum = ChristmasTreeProperties
    silent_properties_enum = ChristmasTreeSilentProperties
    icons_enum = ChristmasTreeIcons
    list_property = LIST_PROPERTY

    def get_custom_properties(
        self,
        properties: Dict[str, Any],
        geom: Dict[str, Any],
        layer_type: str,
        icon_name: str | None,
    ) -> Dict[str, Any]:

        prefix = self.properties_prefix

        return {
            f"{prefix}title": properties.get("title", ""),
            f"{prefix}subtitle": layer_type,
            f"{prefix}icon_type": icon_name,
        }
