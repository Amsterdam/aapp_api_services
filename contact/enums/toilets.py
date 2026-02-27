from contact.enums.base import ChoicesEnum, FilterClass, PropertiesClass
from contact.icons import icon_svg


class ToiletFilters(ChoicesEnum):
    FREE = FilterClass(label="Gratis", filter_key="Prijs_per_gebruik", filter_value=0)
    ACCESSIBLE = FilterClass(
        label="Rolstoeltoegankelijk", filter_key="aapp_is_accessible", filter_value=True
    )
    TOILET = FilterClass(label="Toilet", filter_key="aapp_is_toilet", filter_value=True)


class ToiletProperties(ChoicesEnum):
    NAME = PropertiesClass(
        label=None,
        property_key="Soort",
        property_type="str",
        icon=None,
    )
    OPEN_HOURS = PropertiesClass(
        label="Openingstijden",
        property_key="aapp_open_hours",
        property_type="str",
        icon=icon_svg("clock"),
    )
    PRICE = PropertiesClass(
        label="Prijs",
        property_key="Prijs_per_gebruik",
        property_type="float",
        icon=icon_svg("eurocoins"),
    )
    DESCRIPTION = PropertiesClass(
        label="Omschrijving",
        property_key="aapp_description",
        property_type="str",
        icon=icon_svg("info"),
    )
    IMAGE_URL = PropertiesClass(
        label=None,
        property_key="aapp_image_url",
        property_type="url",
        icon=None,
    )
