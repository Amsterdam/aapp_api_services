from contact.enums.base import ChoicesEnum, IconClass, PropertiesClass
from contact.icons import IconPath


class TapFilters(ChoicesEnum):
    pass


class TapLayers(ChoicesEnum):
    pass


class TapProperties(ChoicesEnum):
    MALFUNCTION = PropertiesClass(
        label=None,
        property_key="aapp_malfunction",
        property_type="malfunction",
        icon=None,
    )
    OPEN_HOURS = PropertiesClass(
        label=None,
        property_key="aapp_type",
        property_type="string",
        icon=None,
    )
    DESCRIPTION = PropertiesClass(
        label=None,
        property_key="beschrijvi",
        property_type="string",
        icon=None,
    )


class TapIcons(ChoicesEnum):
    TAP = IconClass(
        label="tap",
        path=IconPath["tap-tap-marker"],
        circle_color="#009DE6",
        path_color="#FFFFFF",
    )
    FOUNTAIN = IconClass(
        label="fountain",
        path=IconPath["tap-fountain-marker"],
        circle_color="#009DE6",
        path_color="#FFFFFF",
    )
    MALFUNCTION = IconClass(
        label="malfunction",
        path=IconPath["tap-malfunction-marker"],
        circle_color="#767676",
        path_color="#FFFFFF",
    )
