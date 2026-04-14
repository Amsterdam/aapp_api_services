from contact.enums.base import (
    ChoicesEnum,
    DataLayer,
    FilterClass,
    IconClass,
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


class KingsdayLandFilters(ChoicesEnum):
    pass


class KingsdayLandLayers(ChoicesEnum):
    EVENT = FilterClass(
        label="Evenement", filter_key="aapp_subtitle", filter_value="Evenement"
    )
    FIRST_AID = FilterClass(
        label="EHBO-post", filter_key="aapp_subtitle", filter_value="EHBO-post"
    )
    RECYCLE_DROP_OFF = FilterClass(
        label="Inleverpunt overgebleven spullen",
        filter_key="aapp_subtitle",
        filter_value="Inleverpunt overgebleven spullen",
    )
    TOILET = FilterClass(
        label="Toilet", filter_key="aapp_subtitle", filter_value="Toilet"
    )
    DETOUR = FilterClass(
        label="Omleiding", filter_key="aapp_subtitle", filter_value="Omleiding"
    )
    CLOSED_PARKING_LOT = FilterClass(
        label="Afgesloten parkeergarage",
        filter_key="aapp_subtitle",
        filter_value="Afgesloten parkeergarage",
    )


class KingsdayLandProperties(ChoicesEnum):
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


class KingsdayLandIcons(ChoicesEnum):
    EVENT = IconClass(
        label="event",
        path=IconPath["tap-tap-marker"],
        circle_color="#009DE6",
        path_color="#FFFFFF",
    )
    FIRST_AID = IconClass(
        label="first_aid",
        path=IconPath["tap-fountain-marker"],
        circle_color="#009DE6",
        path_color="#FFFFFF",
    )
    RECYCLE_DROP_OFF = IconClass(
        label="recycle_drop_off",
        path=IconPath["tap-malfunction-marker"],
        circle_color="#767676",
        path_color="#FFFFFF",
    )
    TOILET = IconClass(
        label="toilet",
        path=IconPath["tap-fountain-marker"],
        circle_color="#009DE6",
        path_color="#FFFFFF",
    )
    DETOUR = IconClass(
        label="detour",
        path=IconPath["tap-fountain-marker"],
        circle_color="#009DE6",
        path_color="#FFFFFF",
    )
    CLOSED_PARKING_LOT = IconClass(
        label="closed_parking_lot",
        path=IconPath["tap-fountain-marker"],
        circle_color="#009DE6",
        path_color="#FFFFFF",
    )
