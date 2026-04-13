import logging
from typing import Any, Dict

from django.conf import settings

from contact.enums.kingsday_land import (
    KingsdayLandFilters,
    KingsdayLandIcons,
    KingsdayLandProperties,
)
from contact.services.service_abstract import ServiceAbstract

logger = logging.getLogger(__name__)

DATA_LAYERS = {
    "Evenement": "44249",
    # "first_aid": "44267",
    # "spullen_drop_off": "44247",
    # "toilets": "44244",
    # "detours": "44270",
    # "closed_parking_lots": "44270"
}


class KingsdayLandService(ServiceAbstract):
    data_url = settings.KINGSDAY_URL

    def __init__(self) -> None:
        super().__init__()


    def get_full_data(self) -> Dict[str, Any]:

        # all_icons = KingsdayLandIcons.choices()

        base_url = self.data_url

        full_kingsday_land_data = []
        id_counter = 1

        for name, json_nr in DATA_LAYERS.items():
            url = f"{base_url}{json_nr}.json"
            self.data_url = url
            print(f"\n--\nFetching data for {name} from {url}")
            data = self.get_geojson_items()
            print(f"Received {len(data)} items for {name}")
            # icon_type = all_icons.get(name, None)
            # icon_type = KingsdayLandIcons[name.upper()].value.label if name.upper() in KingsdayLandIcons.__members__ else None

            for item in data:
                item_properties = item.get("properties", {})
                item_geom = item.get("geometry", {})
                custom_properties = self.get_custom_properties(item_properties, item_geom, layer_type=name)
                item["properties"] = {**item_properties, **custom_properties}
                item["id"] = id_counter
                id_counter += 1

            print(f"Finished processing data for {name}")
            print(f"Example item for {name}: {data[0] if data else 'No data'}")

            full_kingsday_land_data.extend(data)

        full_data = self.build_response_payload(
            full_kingsday_land_data, KingsdayLandFilters, KingsdayLandProperties, list_property=None, icons=KingsdayLandIcons
        )

        return full_data


    def get_custom_properties(self, properties: Dict[str, Any], geom: Dict[str, Any], layer_type: str) -> Dict[str, Any]:
        """
        Returns a dictionary of custom properties for a tap, using a prefix to avoid conflicts.
        """

        address = self._get_address_from_properties(properties, geom)

        prefix = self.properties_prefix

        return {
            f"{prefix}title": layer_type,
            f"{prefix}subtitle": properties.get("title", ""),
            f"{prefix}icon_type": KingsdayLandIcons.MALFUNCTION.value.label,
            f"{prefix}address": address,
        }

        title = self._tap_title(properties)
        property_type = properties.get("type", "") or ""

        custom_type, malfunction_property, has_malfunction = (
            self._tap_custom_type_and_malfunction(property_type)
        )
        icon_type = self._tap_icon_type(title=title, has_malfunction=has_malfunction)

        return self._build_custom_properties(
            title=title,
            malfunction_property=malfunction_property,
            custom_type=custom_type,
            icon_type=icon_type,
        )

    def _get_address_from_properties(self, properties: Dict[str, Any], geom: Dict[str, Any]) -> str:

        address_properties = {
            "street": properties.get("street", ""),
            "number": properties.get("street_number", ""),
            "postcode": properties.get("zip", ""),
            "city": properties.get("city", ""),
            "coordinates": {
                "lat": geom.get("coordinates")[0] if geom.get("coordinates") else None,
                "lon": geom.get("coordinates")[1] if geom.get("coordinates") else None,
            }
        }
        return address_properties

    # def _tap_title(self, properties: Dict[str, Any]) -> str:
    #     description = (properties.get("beschrijving") or "").lower()
    #     return "Drinkfontein" if "fontein" in description else "Watertap"

    # def _tap_custom_type_and_malfunction(
    #     self, property_type: str
    # ) -> Tuple[str | None, str | None, bool]:
    #     if "storing" in property_type.lower():
    #         return None, "Tijdelijk buiten gebruik", True

    #     if "24-7" in property_type:
    #         return "24 uur per dag beschikbaar", None, False

    #     return property_type, None, False

    # def _tap_icon_type(self, *, title: str, has_malfunction: bool) -> str:
    #     if has_malfunction:
    #         return KingsdayLandIcons.MALFUNCTION.value.label

    #     if title == "Drinkfontein":
    #         return KingsdayLandIcons.FOUNTAIN.value.label

    #     return KingsdayLandIcons.TAP.value.label

    # def _build_custom_properties(
    #     self,
    #     *,
    #     title: str,
    #     malfunction_property: str | None,
    #     custom_type: str | None,
    #     icon_type: str,
    # ) -> Dict[str, Any]:
    #     prefix = self.properties_prefix
    #     return {
    #         f"{prefix}title": title,
    #         f"{prefix}malfunction": malfunction_property,
    #         f"{prefix}type": custom_type,
    #         f"{prefix}icon_type": icon_type,
    #     }

    # def get_geometry_from_properties(
    #     self, properties: Dict[str, Any]
    # ) -> Dict[str, Any]:
    #     """
    #     Original API returns rd coordinates in the geometry field and lat/lon in the properties,
    #     but we want to return lat/lon in the geometry field to be consistent with other services.
    #     """
    #     if (
    #         properties.get("latitude") is not None
    #         and properties.get("longitude") is not None
    #     ):
    #         return {
    #             "type": "Point",
    #             "coordinates": [
    #                 properties.get("longitude"),
    #                 properties.get("latitude"),
    #             ],
    #         }
    #     return {}
