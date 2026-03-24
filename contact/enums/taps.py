from contact.enums.base import ChoicesEnum, IconClass, PropertiesClass


class TapFilters(ChoicesEnum):
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
    TAP = IconClass(icon_id="tap", path="tap", stroke="#009DE6", background="#FF0000")
    FOUNTAIN = IconClass(
        icon_id="fountain", path="fountain", stroke="#009DE6", background="#FFFFFF"
    )
    MALFUNCTION = IconClass(
        icon_id="malfunction",
        path="malfunction",
        stroke="#009DE6",
        background="#FFFFFF",
    )
