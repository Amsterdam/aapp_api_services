from contact.enums.base import (
    ChoicesEnum,
    DataLayer,
    IconClass,
    LayerClass,
    ListPropertyClass,
    PropertiesClass,
)
from contact.icons import IconPath


class PrideMapData(ChoicesEnum):
    CANAL_PARADE = DataLayer(
        label="Canal parade", code=44334, icon_label="canal_parade"
    )
    # EVENTS = DataLayer(label="Evenement", code=44337, icon_label="event") # maybe later added again
    PRIDE_WALK = DataLayer(label="Pride walk", code=44331, icon_label="pride_walk")
    TOILET = DataLayer(label="Toilet", code=44319, icon_label="toilet")
    CLOSURE = DataLayer(label="Afsluiting", code=44322, icon_label="closure")
    WATER_OBSTRUCTION = DataLayer(
        label="Waterstremming", code=44325, icon_label="water_obstruction"
    )


class PrideMapFilters(ChoicesEnum):
    pass


class PrideMapLayers(ChoicesEnum):
    CANAL_PARADE = LayerClass(
        label="Canal parade",
        filter_key="aapp_subtitle",
        filter_value="Canal parade",
        icon_label="canal_parade",
    )
    # EVENT = LayerClass(
    #     label="Evenement",
    #     filter_key="aapp_subtitle",
    #     filter_value="Evenement",
    #     icon_label="event",
    # )
    PRIDE_WALK = LayerClass(
        label="Pride walk",
        filter_key="aapp_subtitle",
        filter_value="Pride walk",
        icon_label="pride_walk",
    )
    TOILET = LayerClass(
        label="Toilet",
        filter_key="aapp_subtitle",
        filter_value="Toilet",
        icon_label="toilet",
    )
    CLOSURE = LayerClass(
        label="Afsluiting",
        filter_key="aapp_subtitle",
        filter_value="Afsluiting",
        icon_label="closure",
    )
    WATER_OBSTRUCTION = LayerClass(
        label="Waterstremming",
        filter_key="aapp_subtitle",
        filter_value="Waterstremming",
        icon_label="water_obstruction",
    )


class PrideMapProperties(ChoicesEnum):
    WHEN = PropertiesClass(
        label="Wanneer",
        property_key="aapp_date_and_time",
        property_type="string",
        icon=IconPath["clock"],
    )
    ADDRESS = PropertiesClass(
        label="Adres",
        property_key="aapp_address",
        property_type="address",
        icon=IconPath["map-marker"],
    )
    TABLE = PropertiesClass(
        label="Overige informatie",
        property_key="aapp_table",
        property_type="key_value_table",
        icon=None,
    )
    WEBSITE = PropertiesClass(
        label=None,
        property_key="aapp_website",
        property_type="url",
        icon=None,
    )


class PrideMapSilentProperties(ChoicesEnum):
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
    START_DATE = PropertiesClass(
        label=None,
        property_key="aapp_start_date",
        property_type="string",
        icon=None,
    )
    END_DATE = PropertiesClass(
        label=None,
        property_key="aapp_end_date",
        property_type="string",
        icon=None,
    )
    START_TIME = PropertiesClass(
        label=None,
        property_key="aapp_start_time",
        property_type="string",
        icon=None,
    )
    END_TIME = PropertiesClass(
        label=None,
        property_key="aapp_end_time",
        property_type="string",
        icon=None,
    )


class PrideMapIcons(ChoicesEnum):
    CANAL_PARADE = IconClass(
        label="canal_parade",
        path=IconPath["info"],
        circle_color="#009DE6",
        path_color="#181818",
    )
    # EVENT = IconClass(
    #     label="event",
    #     path=IconPath["pride-event"],
    #     circle_color="#FF9100",
    #     path_color="#181818",
    # )
    PRIDE_WALK = IconClass(
        label="pride_walk",
        path=IconPath["info"],
        circle_color="#EC0000",
        path_color="#FFFFFF",
    )
    TOILET = IconClass(
        label="toilet",
        path=IconPath["pride-toilet"],
        circle_color="#FFE600",
        path_color="#181818",
    )
    CLOSURE = IconClass(
        label="closure",
        path=IconPath["info"],
        circle_color="#A00078",
        path_color="#FFFFFF",
    )
    WATER_OBSTRUCTION = IconClass(
        label="water_obstruction",
        path=IconPath["info"],
        circle_color="#E50082",
        path_color="#FFFFFF",
    )


LIST_PROPERTY = ListPropertyClass(key="aapp_subtitle", type="string")
