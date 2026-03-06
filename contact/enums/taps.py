from contact.enums.base import (
    ChoicesEnum,
    ListPropertyClass,
    PropertiesClass,
)


class TapFilters(ChoicesEnum):
    pass


class TapProperties(ChoicesEnum):
    OPEN_HOURS = PropertiesClass(
        label="Toegang",
        property_key="type",
        property_type="string",
        icon=None,
    )


LIST_PROPERTY = ListPropertyClass(key="aapp_address", type="address")
