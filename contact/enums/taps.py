from contact.enums.base import ChoicesEnum, FilterClass, PropertiesClass


class TapFilters(ChoicesEnum):
    ALWAYS_ACCESSIBLE = FilterClass(
        label="Always accessible",
        filter_key="aapp_always_accessible",
        filter_value=True,
    )


class TapProperties(ChoicesEnum):
    NAME = PropertiesClass(
        label=None,
        property_key="beschrijvi",
        property_type="str",
        icon=None,
    )
    OPEN_HOURS = PropertiesClass(
        label="Toegang",
        property_key="type",
        property_type="str",
        icon=None,
    )
