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
    BLOCK = DataLayer(label="Afsluiting", code=44255, icon_label="boat_block")
    RECYCLE_BOAT = DataLayer(label="Afvalboot", code=44264, icon_label="recycle_boat")
    # DIRECTION = DataLayer(label="Vaarrichting", code=44261, icon_label="boat_direction")


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
    # DIRECTION = FilterClass(
    #     label="Vaarrichting", filter_key="aapp_subtitle", filter_value="Vaarrichting"
    # )


class KingsdayWaterProperties(ChoicesEnum):
    ADDRESS = PropertiesClass(
        label="Adres",
        property_key="aapp_address",
        property_type="address",
        icon=IconPath["map-marker"],
    )
    WEBSITE = PropertiesClass(
        label=None,
        property_key="aapp_website",
        property_type="url",
        icon=None,
    )
    DESCRIPTION = PropertiesClass(
        label=None,
        property_key="aapp_description",
        property_type="string",
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
        label="boat_block",
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
    # DIRECTION = IconClass(
    #     label="boat_direction",
    #     path=IconPath["tap-tap-marker"],
    #     circle_color="#0000FF",
    #     path_color="#FFFFFF",
    # )


LIST_PROPERTY = ListPropertyClass(key="aapp_subtitle", type="string")
