from contact.enums.base import (
    ChoicesEnum,
    DataLayer,
    FilterClass,
    IconClass,
    ListPropertyClass,
    PropertiesClass,
)
from contact.icons import IconPath


class KingsdayWaterData(ChoicesEnum):
    BOATING_BAN = DataLayer(label="Invaarverbod", code=44258, icon_label="boating_ban")
    BLOCK = DataLayer(label="Afsluiting", code=44255, icon_label="block")
    RECYCLE_BOAT = DataLayer(label="Afvalboot", code=44264, icon_label="recycle_boat")


class KingsdayWaterFilters(ChoicesEnum):
    pass


class KingsdayWaterLayers(ChoicesEnum):
    BOATING_BAN = FilterClass(
        label="Invaarverbod", filter_key="aapp_subtitle", filter_value="Invaarverbod"
    )
    BLOCK = FilterClass(
        label="Afsluiting", filter_key="aapp_subtitle", filter_value="Afsluiting"
    )
    RECYCLE_BOAT = FilterClass(
        label="Afvalboot", filter_key="aapp_subtitle", filter_value="Afvalboot"
    )


class KingsdayWaterProperties(ChoicesEnum):
    SUBTITLE = PropertiesClass(
        label=None,
        property_key="aapp_subtitle",
        property_type="string",
        icon=None,
    )
    ADDRESS = PropertiesClass(
        label=None,
        property_key="aapp_address",
        property_type="address",
        icon=None,
    )
    DESCRIPTION = PropertiesClass(
        label=None,
        property_key="aapp_description",
        property_type="string",
        icon=None,
    )
    WEBSITE = PropertiesClass(
        label=None,
        property_key="aapp_website",
        property_type="url",
        icon=None,
    )


class KingsdayWaterIcons(ChoicesEnum):
    BOATING_BAN = IconClass(
        label="boating_ban",
        path=IconPath["tap-tap-marker"],
        circle_color="#009DE6",
        path_color="#FFFFFF",
    )
    BLOCK = IconClass(
        label="block",
        path=IconPath["tap-tap-marker"],
        circle_color="#FF0000",
        path_color="#FFFFFF",
    )
    RECYCLE_BOAT = IconClass(
        label="recycle_boat",
        path=IconPath["tap-tap-marker"],
        circle_color="#00FF00",
        path_color="#FFFFFF",
    )


LIST_PROPERTY = ListPropertyClass(key="aapp_subtitle", type="string")
