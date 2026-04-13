from contact.enums.base import ChoicesEnum, IconClass, PropertiesClass
from contact.icons import IconPath


class KingsdayLandFilters(ChoicesEnum):
    pass


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
        property_key="description",
        property_type="string",
        icon=None,
    )
    WEBSITE = PropertiesClass(
        label=None,
        property_key="website",
        property_type="url",
        icon=None,
    )


class KingsdayLandIcons(ChoicesEnum):
    EVENT = IconClass(
        label="evenement",
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
    LEFTOVER_STUFF = IconClass(
        label="leftover_stuff",
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
    CLOSED_PARKING_LOTS = IconClass(
        label="closed_parking_lots",
        path=IconPath["tap-fountain-marker"],
        circle_color="#009DE6",
        path_color="#FFFFFF",
    )
