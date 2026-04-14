import logging
import re
from typing import Any, Dict

from django.conf import settings

from contact.enums.kingsday_water import (
    KingsdayWaterData,
    KingsdayWaterFilters,
    KingsdayWaterIcons,
    KingsdayWaterLayers,
    KingsdayWaterProperties,
)
from contact.services.service_abstract import ServiceAbstract

logger = logging.getLogger(__name__)


# as per recommendation from @freylis, compile once only
CLEANR = re.compile("<.*?>")


def cleanhtml(raw_html: str) -> str:
    cleantext = re.sub(CLEANR, "", raw_html)
    return cleantext


class KingsdayWaterService(ServiceAbstract):
    data_url = settings.KINGSDAY_URL

    def __init__(self) -> None:
        super().__init__()
        self.data_layers = KingsdayWaterData.choices_as_list()

    def get_full_data(self) -> Dict[str, Any]:

        base_url = self.data_url

        full_kingsday_water_data = []
        id_counter = 1

        for layer in self.data_layers:
            name = layer["label"]
            url = f"{base_url}{layer['code']}.json"
            self.data_url = url
            data = self.get_geojson_items()

            for item in data:
                item_properties = item.get("properties", {})
                item_geom = item.get("geometry", {})
                custom_properties = self.get_custom_properties(
                    item_properties,
                    item_geom,
                    layer_type=name,
                    icon_name=layer.get("icon_label"),
                )
                item["properties"] = {**item_properties, **custom_properties}
                item["id"] = id_counter
                id_counter += 1

            full_kingsday_water_data.extend(data)

        full_data = self.build_response_payload(
            full_kingsday_water_data,
            KingsdayWaterFilters,
            KingsdayWaterLayers,
            KingsdayWaterProperties,
            list_property=None,
            icons=KingsdayWaterIcons,
        )

        return full_data

    def get_custom_properties(
        self,
        properties: Dict[str, Any],
        geom: Dict[str, Any],
        layer_type: str,
        icon_name: str,
    ) -> Dict[str, Any]:
        """
        Returns a dictionary of custom properties for a tap, using a prefix to avoid conflicts.
        """

        address = self._get_address_from_properties(properties, geom)

        prefix = self.properties_prefix

        return {
            f"{prefix}title": properties.get("title", ""),
            f"{prefix}subtitle": layer_type,
            f"{prefix}icon_type": icon_name,
            f"{prefix}description": cleanhtml(properties.get("description", ""))
            or None,
            f"{prefix}website": properties.get("website", None) or None,
            f"{prefix}address": address,
        }

    def _get_address_from_properties(
        self, properties: Dict[str, Any], geom: Dict[str, Any]
    ) -> str:

        if (
            geom.get("type") == "Point"
            and isinstance(geom.get("coordinates"), list)
            and len(geom.get("coordinates")) == 2
        ):
            # Geometry is already a Point with valid coordinates
            pass

        elif geom.get("type") == "MultiPoint":
            # Geometry type is MultiPoint, which is unexpected. Attempting to use the first point.
            if (
                isinstance(geom.get("coordinates"), list)
                and len(geom.get("coordinates")) > 0
            ):
                geom["coordinates"] = geom["coordinates"][0]
                geom["type"] = "Point"
            else:
                logger.error("MultiPoint geometry does not contain valid coordinates.")

        elif geom.get("type") == "Polygon":
            # Geometry type is Polygon. Use the first coordinate of the first linear ring as a representative point.
            if (
                isinstance(geom.get("coordinates"), list)
                and len(geom.get("coordinates")) > 0
                and isinstance(geom["coordinates"][0], list)
                and len(geom["coordinates"][0]) > 0
            ):
                geom["coordinates"] = geom["coordinates"][0][0]
                geom["type"] = "Point"
            else:
                logger.error("Polygon geometry does not contain valid coordinates.")

        else:
            logger.error(f"Unexpected geometry type: {geom.get('type')}")

        address_properties = {
            "street": properties.get("street", ""),
            "number": properties.get("street_number", ""),
            "postcode": properties.get("zip", ""),
            "city": properties.get("city", "Amsterdam"),
            "coordinates": {
                "lat": geom.get("coordinates")[1] if geom.get("coordinates") else None,
                "lon": geom.get("coordinates")[0] if geom.get("coordinates") else None,
            },
        }
        return address_properties
