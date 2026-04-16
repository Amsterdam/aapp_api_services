from contact.enums.base import (
    ChoicesEnum,
    DataLayer,
    IconClass,
    LayerClass,
    ListPropertyClass,
    PropertiesClass,
)
from contact.icons import IconPath


class KingsdayWaterData(ChoicesEnum):
    BOATING_BAN = DataLayer(label="Invaarverbod", code=44258, icon_label="boating_ban")
    BLOCK = DataLayer(label="Afsluiting", code=44255, icon_label="boat_block")
    RECYCLE_BOAT = DataLayer(label="Afvalboot", code=44264, icon_label="recycle_boat")
    DIRECTION = DataLayer(label="Vaarrichting", code=44261, icon_label="boat_direction")


class KingsdayWaterFilters(ChoicesEnum):
    pass


class KingsdayWaterLayers(ChoicesEnum):
    BOATING_BAN = LayerClass(
        label="Invaarverbod",
        filter_key="aapp_subtitle",
        filter_value="Invaarverbod",
        icon_label="boating_ban",
    )
    BLOCK = LayerClass(
        label="Afsluiting",
        filter_key="aapp_subtitle",
        filter_value="Afsluiting",
        icon_label="boat_block",
    )
    RECYCLE_BOAT = LayerClass(
        label="Afvalboot",
        filter_key="aapp_subtitle",
        filter_value="Afvalboot",
        icon_label="recycle_boat",
    )
    DIRECTION = LayerClass(
        label="Vaarrichting",
        filter_key="aapp_subtitle",
        filter_value="Vaarrichting",
        icon_label="boat_direction",
    )


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


class KingsdayWaterSilentProperties(ChoicesEnum):
    """
    These properties are not shown in the app, but are used for filtering and styling the layers.
    So they should show up for each feature, but not in the properties to include in the app.
    """

    STROKE = PropertiesClass(
        label=None,
        property_key="stroke",
        property_type="string",
        icon=None,
    )
    STROKE_WIDTH = PropertiesClass(
        label=None,
        property_key="stroke-width",
        property_type="integer",
        icon=None,
    )


class KingsdayWaterIcons(ChoicesEnum):
    BOATING_BAN = IconClass(
        label="boating_ban",
        path=IconPath["kingsday-boat-ban"],
        circle_color="#EC0000",
        path_color="#FFFFFF",
    )
    BLOCK = IconClass(
        label="boat_block",
        path=IconPath["kingsday-boat-block"],
        circle_color="#181818",
        path_color="#FFFFFF",
    )
    RECYCLE_BOAT = IconClass(
        label="recycle_boat",
        path=IconPath["kingsday-recycle"],
        circle_color="#00A03C",
        path_color="#FFFFFF",
    )
    DIRECTION = IconClass(
        label="boat_direction",
        path=IconPath["kingsday-boat-direction"],
        circle_color="#FF9100",
        path_color="#181818",
    )


LIST_PROPERTY = ListPropertyClass(key="aapp_subtitle", type="string")
