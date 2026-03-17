from contact.enums.base import (
    ChoicesEnum,
    FilterClass,
    ListPropertyClass,
    PropertiesClass,
)
from contact.icons import IconPath


class ToiletFilters(ChoicesEnum):
    FREE = FilterClass(label="Gratis", filter_key="Prijs_per_gebruik", filter_value=0)
    ACCESSIBLE = FilterClass(
        label="Rolstoeltoegankelijk", filter_key="aapp_is_accessible", filter_value=True
    )
    TOILET = FilterClass(label="Toilet", filter_key="aapp_is_toilet", filter_value=True)


class ToiletProperties(ChoicesEnum):
    OPEN_HOURS = PropertiesClass(
        label="Openingstijden",
        property_key="aapp_opening_hours",
        property_type="string",
        icon=IconPath.get("clock"),
    )
    PRICE = PropertiesClass(
        label="Prijs",
        property_key="Prijs_per_gebruik",
        property_type="price",
        icon=IconPath.get("eurocoins"),
    )
    DESCRIPTION = PropertiesClass(
        label="Omschrijving",
        property_key="aapp_description",
        property_type="string",
        icon=IconPath.get("info"),
    )
    IMAGE_URL = PropertiesClass(
        label=None,
        property_key="aapp_image_url",
        property_type="image",
        icon=None,
    )


LIST_PROPERTY = ListPropertyClass(key="Prijs_per_gebruik", type="price")
