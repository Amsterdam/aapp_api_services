from contact.enums.base import (
    ChoicesEnum,
    PropertiesClass,
)


class TapFilters(ChoicesEnum):
    pass


class TapProperties(ChoicesEnum):
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
