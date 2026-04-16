from contact.enums.base import (
    ChoicesEnum,
    DataLayer,
    IconClass,
    LayerClass,
    ListPropertyClass,
    PropertiesClass,
)
from contact.icons import IconPath


class KingsdayLandData(ChoicesEnum):
    EVENTS = DataLayer(label="Evenement", code=44249, icon_label="event")
    FIRST_AID = DataLayer(label="EHBO-post", code=44267, icon_label="first_aid")
    LEFTOVER_STUFF = DataLayer(
        label="Inleverpunt overgebleven spullen",
        code=44247,
        icon_label="recycle_drop_off",
    )
    TOILET = DataLayer(label="Toilet", code=44244, icon_label="toilet")
    DETOUR = DataLayer(label="Omleiding", code=44270, icon_label="detour")
    CLOSED_PARKING_LOT = DataLayer(
        label="Afgesloten parkeergarage", code=44273, icon_label="closed_parking_lot"
    )
    TAPS = DataLayer(label="Drinkwater", code=0, icon_label="tap")


class KingsdayLandFilters(ChoicesEnum):
    pass


class KingsdayLandLayers(ChoicesEnum):
    EVENT = LayerClass(
        label="Evenement",
        filter_key="aapp_subtitle",
        filter_value="Evenement",
        icon_label="event",
    )
    FIRST_AID = LayerClass(
        label="EHBO-post",
        filter_key="aapp_subtitle",
        filter_value="EHBO-post",
        icon_label="first_aid",
    )
    RECYCLE_DROP_OFF = LayerClass(
        label="Inleverpunt overgebleven spullen",
        filter_key="aapp_subtitle",
        filter_value="Inleverpunt overgebleven spullen",
        icon_label="recycle_drop_off",
    )
    TAP = LayerClass(
        label="Drinkwater",
        filter_key="aapp_subtitle",
        filter_value="Drinkwater",
        icon_label="tap",
    )
    TOILET = LayerClass(
        label="Toilet",
        filter_key="aapp_subtitle",
        filter_value="Toilet",
        icon_label="toilet",
    )
    DETOUR = LayerClass(
        label="Omleiding",
        filter_key="aapp_subtitle",
        filter_value="Omleiding",
        icon_label="detour",
    )
    CLOSED_PARKING_LOT = LayerClass(
        label="Afgesloten parkeergarage",
        filter_key="aapp_subtitle",
        filter_value="Afgesloten parkeergarage",
        icon_label="closed_parking_lot",
    )


class KingsdayLandProperties(ChoicesEnum):
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
    TOILET_TABLE = PropertiesClass(
        label="Overige informatie",
        property_key="aapp_toilet_table",
        property_type="key_value_table",
        icon=None,
    )


class KingsdayLandSilentProperties(ChoicesEnum):
    FILL = PropertiesClass(
        label=None,
        property_key="fill",
        property_type="string",
        icon=None,
    )
    FILL_OPACITY = PropertiesClass(
        label=None,
        property_key="fill-opacity",
        property_type="float",
        icon=None,
    )


class KingsdayLandIcons(ChoicesEnum):
    EVENT = IconClass(
        label="event",
        path=IconPath["kingsday-event"],
        circle_color="#FF9100",
        path_color="#181818",
    )
    FIRST_AID = IconClass(
        label="first_aid",
        path=IconPath["kingsday-first-aid"],
        circle_color="#EC0000",
        path_color="#FFFFFF",
    )
    RECYCLE_DROP_OFF = IconClass(
        label="recycle_drop_off",
        path=IconPath["kingsday-recycle"],
        circle_color="#00A03C",
        path_color="#FFFFFF",
    )
    TAP = IconClass(
        label="tap",
        path=IconPath["kingsday-tap"],
        circle_color="#009DE6",
        path_color="#FFFFFF",
    )
    TOILET = IconClass(
        label="toilet",
        path=IconPath["kingsday-toilet"],
        circle_color="#FFE600",
        path_color="#181818",
    )
    DETOUR = IconClass(
        label="detour",
        path=IconPath["kingsday-detour"],
        circle_color="#A00078",
        path_color="#FFFFFF",
    )
    CLOSED_PARKING_LOT = IconClass(
        label="closed_parking_lot",
        path=IconPath["kingsday-parking-lot"],
        circle_color="#E50082",
        path_color="#FFFFFF",
    )


LIST_PROPERTY = ListPropertyClass(key="aapp_subtitle", type="string")
